
import multiprocessing as mp
from multiprocessing import shared_memory
import ctypes
import time
import math
import statistics

from harness import emit_verify_tag


STUDENT_ID = 230103360

P_PHYS = 10
N = 256

BUFFER_SIZE = 64 * 1024 * 1024

TILE_SIZES = [8, 16, 32, 64, 96, 128]
GEMM_RUNS = 3

FLOPS_PER_WORKER = 60_000_000

MASK = 0xFFFFFFFFFFFFFFFF


# ==================================================
# PART 3A: DRAM BANDWIDTH
# ==================================================

def copy_worker(src_name, dst_name, start, end):

    src = shared_memory.SharedMemory(name=src_name)
    dst = shared_memory.SharedMemory(name=dst_name)

    source = src.buf[start:end]
    destination = dst.buf[start:end]

    try:
        destination[:] = source
    finally:
        source.release()
        destination.release()
        src.close()
        dst.close()


def measure_bandwidth():

    src = shared_memory.SharedMemory(
        create=True, size=BUFFER_SIZE
    )

    dst = shared_memory.SharedMemory(
        create=True, size=BUFFER_SIZE
    )

    processes = []

    try:
        # Initialize source buffer
        src.buf[:] = b'\x01' * BUFFER_SIZE

        chunk = BUFFER_SIZE // P_PHYS

        start = time.perf_counter_ns()

        for worker in range(P_PHYS):

            begin = worker * chunk
            end = (
                (worker + 1) * chunk
                if worker < P_PHYS - 1
                else BUFFER_SIZE
            )

            process = mp.Process(
                target=copy_worker,
                args=(src.name, dst.name, begin, end)
            )

            processes.append(process)
            process.start()

        for process in processes:
            process.join()

            if process.exitcode != 0:
                raise RuntimeError("Memory copy worker failed")

        end = time.perf_counter_ns()

        elapsed = (end - start) / 1e9

        bandwidth = (
            2 * BUFFER_SIZE / elapsed / 1e9
        )

        return elapsed * 1000, bandwidth

    finally:
        src.close()
        src.unlink()
        dst.close()
        dst.unlink()


# ==================================================
# COMPUTE CEILING
# ==================================================

def compute_worker():

    iterations = FLOPS_PER_WORKER // 32

    x0 = 0.1
    x1 = 0.2
    x2 = 0.3
    x3 = 0.4
    x4 = 0.5
    x5 = 0.6
    x6 = 0.7
    x7 = 0.8
    x8 = 0.9
    x9 = 1.0
    x10 = 1.1
    x11 = 1.2
    x12 = 1.3
    x13 = 1.4
    x14 = 1.5
    x15 = 1.6

    a = 1.00000001
    b = 0.00000001

    for _ in range(iterations):

        x0 = x0 * a + b
        x1 = x1 * a + b
        x2 = x2 * a + b
        x3 = x3 * a + b
        x4 = x4 * a + b
        x5 = x5 * a + b
        x6 = x6 * a + b
        x7 = x7 * a + b

        x8 = x8 * a + b
        x9 = x9 * a + b
        x10 = x10 * a + b
        x11 = x11 * a + b
        x12 = x12 * a + b
        x13 = x13 * a + b
        x14 = x14 * a + b
        x15 = x15 * a + b

    return (
        x0 + x1 + x2 + x3 +
        x4 + x5 + x6 + x7 +
        x8 + x9 + x10 + x11 +
        x12 + x13 + x14 + x15
    )


def measure_compute():

    with mp.Pool(processes=P_PHYS) as pool:

        start = time.perf_counter_ns()

        results = pool.map(
            compute_task,
            range(P_PHYS)
        )

        end = time.perf_counter_ns()

    elapsed = (end - start) / 1e9

    total_flops = FLOPS_PER_WORKER * P_PHYS

    gflops = total_flops / elapsed / 1e9

    return elapsed * 1000, gflops, sum(results)


def compute_task(_):
    return compute_worker()


# ==================================================
# PART 3B: MATRIX INITIALIZATION
# ==================================================

def initialize_matrices():

    a = [
        ((i * 7 + 3) % 101) / 101.0
        for i in range(N * N)
    ]

    b = [
        ((i * 11 + 5) % 97) / 97.0
        for i in range(N * N)
    ]

    return a, b


# ==================================================
# GEMM WORKERS
# ==================================================

def gemm_worker(
    a_name,
    b_name,
    c_name,
    start_row,
    end_row,
    variant,
    block_size=32
):

    shm_a = shared_memory.SharedMemory(name=a_name)
    shm_b = shared_memory.SharedMemory(name=b_name)
    shm_c = shared_memory.SharedMemory(name=c_name)

    A = (ctypes.c_double * (N * N)).from_buffer(shm_a.buf)
    B = (ctypes.c_double * (N * N)).from_buffer(shm_b.buf)
    C = (ctypes.c_double * (N * N)).from_buffer(shm_c.buf)

    if variant == 1:

        # Naive i-j-k
        for i in range(start_row, end_row):

            for j in range(N):

                total = 0.0

                for k in range(N):
                    total += A[i * N + k] * B[k * N + j]

                C[i * N + j] = total

    elif variant == 2:

        # Reordered i-k-j
        for i in range(start_row, end_row):

            row_offset = i * N

            for k in range(N):

                aik = A[row_offset + k]
                b_offset = k * N

                for j in range(N):

                    C[row_offset + j] += (
                        aik * B[b_offset + j]
                    )

    elif variant == 3:

        # Cache-blocked i-k-j
        for ii in range(start_row, end_row, block_size):

            i_end = min(ii + block_size, end_row)

            for jj in range(0, N, block_size):

                j_end = min(jj + block_size, N)

                for kk in range(0, N, block_size):

                    k_end = min(kk + block_size, N)

                    for i in range(ii, i_end):

                        row_offset = i * N

                        for k in range(kk, k_end):

                            aik = A[row_offset + k]
                            b_offset = k * N

                            for j in range(jj, j_end):

                                C[row_offset + j] += (
                                    aik * B[b_offset + j]
                                )

    del A
    del B
    del C

    shm_a.close()
    shm_b.close()
    shm_c.close()


# ==================================================
# GEMM BENCHMARK
# ==================================================

def run_gemm(a_values, b_values, variant, block_size=32):

    shm_a = shared_memory.SharedMemory(
        create=True, size=N * N * 8
    )

    shm_b = shared_memory.SharedMemory(
        create=True, size=N * N * 8
    )

    shm_c = shared_memory.SharedMemory(
        create=True, size=N * N * 8
    )

    try:

        A = (ctypes.c_double * (N * N)).from_buffer(shm_a.buf)
        B = (ctypes.c_double * (N * N)).from_buffer(shm_b.buf)
        C = (ctypes.c_double * (N * N)).from_buffer(shm_c.buf)

        for i in range(N * N):
            A[i] = a_values[i]
            B[i] = b_values[i]
            C[i] = 0.0

        del A
        del B
        del C

        rows_per_worker = N // P_PHYS

        processes = []

        start = time.perf_counter_ns()

        for worker in range(P_PHYS):

            first = worker * rows_per_worker

            last = (
                (worker + 1) * rows_per_worker
                if worker < P_PHYS - 1
                else N
            )

            process = mp.Process(
                target=gemm_worker,
                args=(
                    shm_a.name,
                    shm_b.name,
                    shm_c.name,
                    first,
                    last,
                    variant,
                    block_size
                )
            )

            processes.append(process)
            process.start()

        for process in processes:
            process.join()

            if process.exitcode != 0:
                raise RuntimeError("GEMM worker failed")

        end = time.perf_counter_ns()

        result = (
            ctypes.c_double * (N * N)
        ).from_buffer(shm_c.buf)

        output = list(result)

        del result

        elapsed = (end - start) / 1e6

        return elapsed, output

    finally:

        shm_a.close()
        shm_b.close()
        shm_c.close()

        shm_a.unlink()
        shm_b.unlink()
        shm_c.unlink()


# ==================================================
# REPEATED GEMM MEASUREMENTS
# ==================================================

def benchmark_gemm(a_values, b_values, variant, block_size=32):
    samples = []
    final_output = None

    for run in range(GEMM_RUNS):
        elapsed, output = run_gemm(
            a_values, b_values, variant, block_size
        )
        samples.append(elapsed)
        final_output = output
        print(f"  Run {run + 1}/{GEMM_RUNS}: {elapsed:.2f} ms")

    median_ms = statistics.median(samples)
    return median_ms, final_output, samples


# ==================================================
# ANALYSIS
# ==================================================

def calculate_gflops(elapsed_ms):

    operations = 2 * (N ** 3)

    return operations / (elapsed_ms * 1e6)


def compare_results(reference, result):

    return max(
        abs(x - y)
        for x, y in zip(reference, result)
    )


def main():

    print("=" * 65)
    print("PHASE 3: EMPIRICAL ROOFLINE & GEMM")
    print("=" * 65)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Physical cores: {P_PHYS}")
    print(f"Matrix size: {N} x {N}")

    # ==========================================
    # PART 3A: ROOFLINE
    # ==========================================

    print("\nPART 3A: DRAM BANDWIDTH")

    bandwidth_samples = []
    bandwidth_results = []

    for run in range(3):

        elapsed, bandwidth = measure_bandwidth()

        bandwidth_samples.append(bandwidth)
        bandwidth_results.append(elapsed)

        print(
            f"Run {run + 1}: "
            f"{elapsed:.2f} ms | "
            f"{bandwidth:.4f} GB/s"
        )

    median_bandwidth = statistics.median(
        bandwidth_samples
    )

    print(
        f"\nMedian bandwidth: "
        f"{median_bandwidth:.4f} GB/s"
    )

    print("\nCOMPUTE CEILING")

    compute_times = []
    compute_results = []

    for run in range(3):

        elapsed, gflops, checksum = measure_compute()

        compute_times.append(elapsed)
        compute_results.append(gflops)

        print(
            f"Run {run + 1}: "
            f"{elapsed:.2f} ms | "
            f"{gflops:.4f} GFLOP/s"
        )

    median_compute = statistics.median(
        compute_results
    )

    ridge_point = median_compute / median_bandwidth

    print(f"\nMedian compute: {median_compute:.4f} GFLOP/s")
    print(f"Ridge Point: {ridge_point:.4f} FLOP/byte")

    # ==========================================
    # PART 3B: GEMM
    # ==========================================

    print("\nPART 3B: GEMM")

    a_values, b_values = initialize_matrices()

    print("\nVariant 1: Naive i-j-k")

    time_v1, result_v1, samples_v1 = benchmark_gemm(
        a_values, b_values, 1
    )

    gflops_v1 = calculate_gflops(time_v1)

    print(f"Median time: {time_v1:.2f} ms")
    print(f"Performance from median: {gflops_v1:.4f} GFLOP/s")

    print("\nVariant 2: Reordered i-k-j")

    time_v2, result_v2, samples_v2 = benchmark_gemm(
        a_values, b_values, 2
    )

    gflops_v2 = calculate_gflops(time_v2)

    print(f"Median time: {time_v2:.2f} ms")
    print(f"Performance from median: {gflops_v2:.4f} GFLOP/s")

    error_v2 = compare_results(result_v1, result_v2)

    print(f"Maximum error V1 vs V2: {error_v2:.12e}")

    if error_v2 >= 1e-9:
        raise RuntimeError("Variant 2 verification failed")

    # ==========================================
    # VARIANT 3: TILE SWEEP
    # ==========================================

    print("\nVariant 3: Cache-Blocked GEMM")

    tile_results = {}

    for bs in TILE_SIZES:

        print(f"\nTesting BS = {bs}")

        elapsed, result, samples = benchmark_gemm(
            a_values, b_values, 3, bs
        )

        gflops = calculate_gflops(elapsed)

        error = compare_results(result_v1, result)

        tile_footprint = 3 * bs * bs * 8
        intensity = bs / 12

        tile_results[bs] = {
            "time": elapsed,
            "gflops": gflops,
            "error": error,
            "footprint": tile_footprint,
            "intensity": intensity
        }

        print(f"Median time: {elapsed:.2f} ms")
        print(f"Performance from median: {gflops:.4f} GFLOP/s")
        print(f"Max error: {error:.12e}")
        print(f"Tile footprint: {tile_footprint} bytes")
        print(f"Operational intensity: {intensity:.4f} FLOP/byte")

        if error >= 1e-9:
            raise RuntimeError(
                f"Verification failed for BS={bs}"
            )

    best_bs = max(
        tile_results,
        key=lambda bs: tile_results[bs]["gflops"]
    )

    best_gflops = tile_results[best_bs]["gflops"]

    print("\n" + "=" * 65)
    print("GEMM SUMMARY")
    print("=" * 65)

    print(f"Variant 1: {gflops_v1:.4f} GFLOP/s")
    print(f"Variant 2: {gflops_v2:.4f} GFLOP/s")
    print(f"Best tile size: {best_bs}")
    print(f"Variant 3: {best_gflops:.4f} GFLOP/s")

    # ==========================================
    # VERIFICATION HASH
    # ==========================================

    verify = emit_verify_tag(
        "PHASE3",
        STUDENT_ID,
        gflops_v1,
        best_gflops
    )

    print("\n" + "=" * 65)
    print(verify)
    print("=" * 65)


if __name__ == "__main__":
    mp.freeze_support()
    main()
