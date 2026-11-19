#!/usr/bin/env python3
"""Four-rank MPI + CUDA reaction-diffusion stencil for the lab.
Run: mpirun --allow-run-as-root --oversubscribe -np 4 python3 distributed_cuda_solver.py GITHUB_USERNAME
Execution in the target Colab runtime is required; this file is not claimed tested there.
"""
import sys, hashlib, subprocess, json, time
import numpy as np
from mpi4py import MPI
from numba import cuda, float64

N, P, T, LAM = 256, 16, 400, 0.15
PAD, DX, DT = 258, 1.0/513.0, 1e-6

@cuda.jit
def pack(u, t, b, l, r):
    i = cuda.grid(1)
    if i < 256:
        t[i]=u[1,i+1]; b[i]=u[256,i+1]
        l[i]=u[i+1,1]; r[i]=u[i+1,256]

@cuda.jit
def unpack(u, t, b, l, r, ht, hb, hl, hr):
    i=cuda.grid(1)
    if i<256:
        u[0,i+1]=t[i] if ht else 0.0
        u[257,i+1]=b[i] if hb else 0.0
        u[i+1,0]=l[i] if hl else 0.0
        u[i+1,257]=r[i] if hr else 0.0

@cuda.jit
def stencil(u,k,s,v,dt,r0,r1,c0,c1):
    a=cuda.shared.array((18,18),float64)
    q=cuda.shared.array((18,18),float64)
    x=cuda.threadIdx.x; y=cuda.threadIdx.y
    gx=1+cuda.blockIdx.x*16+x; gy=1+cuda.blockIdx.y*16+y
    a[y+1,x+1]=u[gy,gx]; q[y+1,x+1]=k[gy,gx]
    if x==0: a[y+1,0]=u[gy,gx-1]; q[y+1,0]=k[gy,gx-1]
    if x==15: a[y+1,17]=u[gy,gx+1]; q[y+1,17]=k[gy,gx+1]
    if y==0: a[0,x+1]=u[gy-1,gx]; q[0,x+1]=k[gy-1,gx]
    if y==15: a[17,x+1]=u[gy+1,gx]; q[17,x+1]=k[gy+1,gx]
    if x==0 and y==0: a[0,0]=u[gy-1,gx-1]; q[0,0]=k[gy-1,gx-1]
    if x==15 and y==0: a[0,17]=u[gy-1,gx+1]; q[0,17]=k[gy-1,gx+1]
    if x==0 and y==15: a[17,0]=u[gy+1,gx-1]; q[17,0]=k[gy+1,gx-1]
    if x==15 and y==15: a[17,17]=u[gy+1,gx+1]; q[17,17]=k[gy+1,gx+1]
    cuda.syncthreads()
    if r0<=gy<=r1 and c0<=gx<=c1:
        z=a[y+1,x+1]; kc=q[y+1,x+1]
        ke=.5*(kc+q[y+1,x+2]); kw=.5*(kc+q[y+1,x])
        ks=.5*(kc+q[y+2,x+1]); kn=.5*(kc+q[y,x+1])
        lap=(ke*(a[y+1,x+2]-z)-kw*(z-a[y+1,x])+ks*(a[y+2,x+1]-z)-kn*(z-a[y,x+1]))/(DX*DX)
        v[gy,gx]=z+dt*(lap-LAM*z*z*z+s[gy,gx])

def seed_for(user, uuid):
    return int(hashlib.sha256(f"{user.strip()}::{uuid}".encode()).hexdigest()[:16],16)

def topology(user):
    w=MPI.COMM_WORLD
    if w.size!=4: raise RuntimeError(f"Expected 4 MPI ranks, got {w.size}")
    c=w.Create_cart([2,2],periods=[False,False],reorder=False)
    rank=c.rank; coords=c.Get_coords(rank)
    up,down=c.Shift(0,1); left,right=c.Shift(1,1)
    cuda.select_device(0)
    uuid=subprocess.check_output(["nvidia-smi","--query-gpu=uuid","--format=csv,noheader"],text=True).strip().splitlines()[0]
    return c,rank,coords,(up,down,left,right),uuid,seed_for(user,uuid)

def init_fields(coords,seed,nb):
    rr,cc=coords
    yy=(rr*256+np.arange(258)-1+.5)/512
    xx=(cc*256+np.arange(258)-1+.5)/512
    X,Y=np.meshgrid(xx,yy); rng=np.random.default_rng(seed)
    centers=rng.uniform(.15,.85,(3,2)); amps=rng.uniform(.5,1.,3)
    u=np.zeros((258,258))
    for (cx,cy),amp in zip(centers,amps): u+=amp*np.exp(-((X-cx)**2+(Y-cy)**2)/.008)
    k=.08+.16*(.5+.5*np.sin(2*np.pi*X)*np.cos(2*np.pi*Y))
    s=.02*np.exp(-((X-.5)**2+(Y-.5)**2)/.01)
    if nb[0]==MPI.PROC_NULL:u[0,:]=0
    if nb[1]==MPI.PROC_NULL:u[257,:]=0
    if nb[2]==MPI.PROC_NULL:u[:,0]=0
    if nb[3]==MPI.PROC_NULL:u[:,257]=0
    return u,k.astype(np.float64),s.astype(np.float64)

def buffers():
    sh=[cuda.pinned_array(256,np.float64) for _ in range(4)]
    rh=[cuda.pinned_array(256,np.float64) for _ in range(4)]
    sd=[cuda.device_array(256,np.float64) for _ in range(4)]
    rd=[cuda.device_array(256,np.float64) for _ in range(4)]
    return sh,rh,sd,rd

def exchange(c,nb,u,stream,B):
    up,dn,lf,rt=nb; sh,rh,sd,rd=B
    pack[1,256,stream](u,*sd)
    for i in range(4): sd[i].copy_to_host(sh[i],stream=stream); rh[i].fill(0)
    stream.synchronize()
    req=[c.Irecv(rh[0],up,tag=1),c.Irecv(rh[1],dn,tag=0),c.Irecv(rh[2],lf,tag=3),c.Irecv(rh[3],rt,tag=2),
         c.Isend(sh[0],up,tag=0),c.Isend(sh[1],dn,tag=1),c.Isend(sh[2],lf,tag=2),c.Isend(sh[3],rt,tag=3)]
    return req

def finish(c,nb,u,stream,B,req):
    MPI.Request.Waitall(req); sh,rh,sd,rd=B
    for i in range(4): rd[i].copy_to_device(rh[i],stream=stream)
    unpack[1,256,stream](u,*rd,*(x!=MPI.PROC_NULL for x in nb))
    stream.synchronize()

def launch(u,k,s,v,st,box):
    stencil[(16,16),(16,16),st](u,k,s,v,DT,*box)

def serialized(c,nb,u,k,s,v,st,B):
    req=exchange(c,nb,u,st,B); finish(c,nb,u,st,B,req)
    launch(u,k,s,v,st,(1,256,1,256)); st.synchronize()
    return v

def overlapped(c,nb,u,k,s,v,sb,si,B):
    req=exchange(c,nb,u,sb,B)
    launch(u,k,s,v,si,(2,255,2,255))
    finish(c,nb,u,sb,B,req)
    for box in [(1,1,1,256),(256,256,1,256),(2,255,1,1),(2,255,256,256)]:
        launch(u,k,s,v,sb,box)
    sb.synchronize(); si.synchronize()
    return v

def energy(c,u):
    val=float(np.sum(u.copy_to_host()[1:257,1:257]**2))
    return c.allreduce(val,op=MPI.SUM)

def main():
    if len(sys.argv)!=2: raise SystemExit("Pass your real GitHub username as the only argument.")
    c,rank,coords,nb,uuid,seed=topology(sys.argv[1])
    hu,hk,hs=init_fields(coords,seed,nb)
    k=cuda.to_device(hk); s=cuda.to_device(hs)
    sb,si=cuda.stream(),cuda.stream(); B=buffers()
    us=cuda.to_device(hu); vs=cuda.device_array((258,258),np.float64)
    c.Barrier(); t0=time.perf_counter()
    for _ in range(T):
        us=serialized(c,nb,us,k,s,vs,sb,B); vs,us=us,vs
    sb.synchronize(); serial_ms=(time.perf_counter()-t0)*1000
    uo=cuda.to_device(hu); vo=cuda.device_array((258,258),np.float64)
    trace=[{"step":0,"energy":energy(c,uo)}]
    c.Barrier(); t1=time.perf_counter()
    for step in range(1,T+1):
        uo=overlapped(c,nb,uo,k,s,vo,sb,si,B); vo,uo=uo,vo
        if step%100==0: trace.append({"step":step,"energy":energy(c,uo)})
    sb.synchronize(); si.synchronize(); overlap_ms=(time.perf_counter()-t1)*1000
    diff=float(np.max(np.abs(us.copy_to_host()[1:257,1:257]-uo.copy_to_host()[1:257,1:257])))
    diff=c.allreduce(diff,op=MPI.MAX)
    asm=stencil.inspect_asm(stencil.signatures[0])
    audit={"ld.shared":asm.count("ld.shared"),"st.shared":asm.count("st.shared"),"bar.sync":asm.count("bar.sync")}
    rows=c.gather({"rank":rank,"serial_ms":serial_ms,"overlap_ms":overlap_ms},root=0)
    if rank==0:
        print(json.dumps({"mpi_ranks":4,"cartesian_dims":[2,2],"gpu_uuid":uuid,"instance_seed":seed,
          "serialized_ms_max_rank":max(x["serial_ms"] for x in rows),
          "overlapped_ms_max_rank":max(x["overlap_ms"] for x in rows),
          "parity_max_diff":diff,"energy_trace":trace,"ptx_audit":audit},indent=2))
    c.Barrier()

if __name__=="__main__": main()
