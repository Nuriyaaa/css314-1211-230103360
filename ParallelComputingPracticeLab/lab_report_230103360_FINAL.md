# Performance Evaluation and Optimization in Parallel Computing

**Student ID:** 230103360  
**CPU:** Apple M4  
**Operating System:** macOS  
**Python Version:** 3.14.3

---

## Phase 0 — Hardware Topology & Minimal Telemetry

### Hardware Specifications

| Parameter | Value |
|---|---:|
| CPU Model | Apple M4 |
| Physical Cores | 10 |
| Logical Threads | 10 |
| Cache Line Size | 128 bytes |
| L1d Cache | 64 KB |
| L2 Cache | 4 MB |
| L3 Cache | Not reported by the system query |

### Calibration Results

| Metric | Result |
|---|---:|
| Student ID | 230103360 |
| CPU Count | 10 |
| Number of Calls | 1,000,000 |
| Total Time | 55.1953 ms |
| Average Call Latency | 55.1953 ns |

### Verification

```text
VERIFY_HASH[PHASE0]: 0A1B436D8B26AC19 (P_log=10)
```

---

## Phase 1 — False Sharing Stride Sweep & Karp-Flatt Diagnostics

### Experimental Configuration

- SharedMemory size: 4096 bytes
- Total operations: 16,000,000
- Physical cores: 10
- Logical threads: 10
- Stride values: 1, 2, 4, 8, 16, 32
- Repeated measurements: 3

### 1. Stride Sweep Results

| Stride | Distance (bytes) | Median (ms) | IQR (ms) | Throughput (Mops/s) |
|---:|---:|---:|---:|---:|
| 1 | 8 | 376.79 | 23.15 | 42.4638 |
| 2 | 16 | 365.12 | 5.02 | 43.8216 |
| 4 | 32 | 358.65 | 7.38 | 44.6121 |
| 8 | 64 | 355.30 | 18.19 | 45.0328 |
| 16 | 128 | 375.18 | 12.63 | 42.6460 |
| 32 | 256 | 355.24 | 9.64 | 45.0405 |

### 2. Process Scaling Results

#### Stride = 1

| Processes | Median (ms) | Speedup | Efficiency | Karp-Flatt |
|---:|---:|---:|---:|---:|
| 1 | 1635.76 | 1.0000 | 1.0000 | N/A |
| 2 | 867.95 | 1.8846 | 0.9423 | 0.06122 |
| 4 | 518.06 | 3.1575 | 0.7894 | 0.08895 |
| 8 | 387.99 | 4.2160 | 0.5270 | 0.12822 |
| 10 | 376.28 | 4.3472 | 0.4347 | 0.14448 |

#### Stride = 16

| Processes | Median (ms) | Speedup | Efficiency | Karp-Flatt |
|---:|---:|---:|---:|---:|
| 1 | 1650.16 | 1.0000 | 1.0000 | N/A |
| 2 | 899.18 | 1.8352 | 0.9176 | 0.08981 |
| 4 | 517.28 | 3.1900 | 0.7975 | 0.08463 |
| 8 | 395.79 | 4.1693 | 0.5212 | 0.13126 |
| 10 | 386.62 | 4.2681 | 0.4268 | 0.14922 |

### 3. Hardware-Based Analysis

The Apple M4 has a cache line size of 128 bytes. With stride = 1, different workers update adjacent 64-bit slots, which can cause false sharing.

Increasing the stride to 16 separates worker slots by 128 bytes. However, the measured median time for stride = 16 was 375.18 ms, compared with 376.79 ms for stride = 1. This difference was very small, so the experiment did not demonstrate a substantial performance improvement from padding alone.

The best measured throughput was 45.0405 Mops/s at stride = 32. Process scaling improved performance as the number of processes increased. However, efficiency decreased from 94.23% at 2 processes to 43.47% at 10 processes for stride = 1.

The Karp-Flatt serial fraction increased with the process count, indicating growing parallel overhead and diminishing returns. The stride = 16 scaling results did not consistently outperform stride = 1. This suggests that process scheduling, memory behavior, and measurement variability also influenced the experiment.

### 4. Verification

```text
VERIFY_HASH[PHASE1]: 536A918A59CA4ED4 (P_log=10)
```

---

## Phase 2 — Strong Scaling vs. Weak Scaling

### Experimental Configuration

- CPU: Apple M4
- Physical cores: 10
- Logical CPUs: 10
- Strong workload: 1,200,000 elements
- Weak workload per worker: 200,000 elements
- Repeated measurements: 3
- Process counts: 1–10, plus 11 for the oversubscription experiment
- Stage B: 30 operations per element, implemented as 10 repetitions of `sin`, `sqrt`, and `fma`

### 1. Strong Scaling Results

| Processes | Time (ms) | Speedup | Efficiency |
|---:|---:|---:|---:|
| 1 | 881.27 | 1.0000 | 1.0000 |
| 2 | 478.44 | 1.8420 | 0.9210 |
| 3 | 311.64 | 2.8278 | 0.9426 |
| 4 | 252.61 | 3.4886 | 0.8722 |
| 5 | 238.98 | 3.6876 | 0.7375 |
| 6 | 235.77 | 3.7378 | 0.6230 |
| 7 | 213.42 | 4.1292 | 0.5899 |
| 8 | 201.42 | 4.3752 | 0.5469 |
| 9 | 190.19 | 4.6337 | 0.5149 |
| 10 | 182.71 | 4.8233 | 0.4823 |

Serial fraction: **0.020259**  
Amdahl theoretical cap: **49.3600**

### 2. Weak Scaling Results

| Processes | Total N | Time (ms) | Weak Efficiency | Gustafson Speedup |
|---:|---:|---:|---:|---:|
| 1 | 200,000 | 145.98 | 1.0000 | 1.0000 |
| 2 | 400,000 | 153.10 | 0.9535 | 1.9594 |
| 3 | 600,000 | 156.81 | 0.9309 | 2.8822 |
| 4 | 800,000 | 173.38 | 0.8420 | 3.7707 |
| 5 | 1,000,000 | 212.34 | 0.6875 | 4.6947 |
| 6 | 1,200,000 | 229.25 | 0.6368 | 5.5771 |
| 7 | 1,400,000 | 263.86 | 0.5532 | 6.2078 |
| 8 | 1,600,000 | 269.42 | 0.5418 | 7.3065 |
| 9 | 1,800,000 | 288.25 | 0.5064 | 8.1687 |
| 10 | 2,000,000 | 310.55 | 0.4701 | 9.0848 |

### 3. Architectural Inflection / Oversubscription

| Metric | Result |
|---|---:|
| Time at 10 processes | 182.71 ms |
| Time at 11 processes | 184.39 ms |
| Marginal speedup (T10 / T11) | 0.9909 |
| Marginal gain | -0.91% |

The Apple M4 has 10 logical CPUs. Therefore, the 11-process experiment represents oversubscription rather than a transition between SMT threads or processor core types. The additional process increased execution time by approximately 0.91%.

### 4. Hardware-Based Analysis

Strong scaling improved as the process count increased. The best measured speedup at 10 processes was 4.8233, with a parallel efficiency of 48.23%.

The estimated serial fraction was approximately 2.03%, resulting in an Amdahl theoretical speedup limit of 49.3600. In practice, the measured speedup was lower because of process management, scheduling, and parallel execution overhead.

In weak scaling, execution time increased from 145.98 ms to 310.55 ms as the workload increased from 200,000 to 2,000,000 elements. Weak efficiency decreased to 47.01%, indicating that the system could not maintain constant execution time as the workload increased.

Gustafson's scaled speedup reached 9.0848 at 10 processes, demonstrating the potential benefit of increasing the workload with the number of processes.

The additional 11-process experiment produced a marginal speedup of 0.9909 compared with 10 processes. Execution time increased by approximately 0.91%. This indicates that oversubscribing the 10 logical CPUs did not improve performance for this workload.

### 5. Verification

```text
VERIFY_HASH[PHASE2]: 42EDB09D9DE6B422 (P_log=10)
```

---

## Phase 3 — Empirical Roofline & Cache-Blocked GEMM

### Experimental Configuration

- CPU: Apple M4
- Physical cores: 10
- Matrix dimensions: 256 × 256
- Data type: double precision (64-bit)
- Shared memory buffers: 2 × 64 MB
- Tile sizes: 8, 16, 32, 64, 96, 128
- GEMM measurements: 3 runs per variant / tile size; median reported

### 1. DRAM Bandwidth

| Run | Time (ms) | Bandwidth (GB/s) |
|---:|---:|---:|
| 1 | 108.89 | 1.2326 |
| 2 | 88.18 | 1.5221 |
| 3 | 86.25 | 1.5561 |

Median DRAM Bandwidth: **1.5221 GB/s**

### 2. Compute Ceiling

| Run | Time (ms) | Performance (GFLOP/s) |
|---:|---:|---:|
| 1 | 656.80 | 0.9135 |
| 2 | 682.82 | 0.8787 |
| 3 | 704.25 | 0.8520 |

Median Compute Performance: **0.8787 GFLOP/s**

Ridge Point:

\[
0.8787 / 1.5221 = 0.5773\ \text{FLOP/byte}
\]

### 3. GEMM Variant Comparison

| Variant | Median Time (ms) | Performance (GFLOP/s) |
|---|---:|---:|
| Naive i-j-k | 341.04 | 0.0984 |
| Reordered i-k-j | 372.71 | 0.0900 |
| Cache-Blocked BS=128 | 380.26 | 0.0882 |

Maximum numerical error:

- Variant 1 vs Variant 2: `0.0`
- Variant 1 vs Variant 3: `0.0` for all tested tile sizes

### 4. Cache Tile Sweep

| BS | Tile Footprint (bytes) | Operational Intensity (FLOP/byte) | Performance (GFLOP/s) |
|---:|---:|---:|---:|
| 8 | 1,536 | 0.6667 | 0.0846 |
| 16 | 6,144 | 1.3333 | 0.0811 |
| 32 | 24,576 | 2.6667 | 0.0877 |
| 64 | 98,304 | 5.3333 | 0.0869 |
| 96 | 221,184 | 8.0000 | 0.0879 |
| 128 | 393,216 | 10.6667 | 0.0882 |

Best measured tile size: **BS = 128**

### 5. Hardware-Based Analysis

The measured DRAM bandwidth was 1.5221 GB/s, while the median compute performance was 0.8787 GFLOP/s. The calculated Ridge Point was 0.5773 FLOP/byte.

Among the tested GEMM variants, the Naive i-j-k implementation achieved the highest measured performance of 0.0984 GFLOP/s. The Reordered i-k-j variant achieved 0.0900 GFLOP/s. Although it provides unit-stride access to matrix B, it did not outperform the naive implementation in this Python experiment.

The Cache-Blocked implementation achieved its best measured performance at BS = 128, reaching 0.0882 GFLOP/s. Its tile footprint was 393,216 bytes, which is larger than the measured L1d cache of 64 KB but smaller than the L2 cache of 4 MB.

All tested implementations passed the numerical comparison with a maximum error of 0.0, below the required tolerance of 1e-9. These measurements represent Python implementation performance, including process and interpreter overhead, rather than the theoretical peak performance of the Apple M4 processor.

### 6. Verification

```text
VERIFY_HASH[PHASE3]: E95E95D1DA76998D (P_log=10)
```

---

## Phase 4 — Skewed Workloads and Dynamic Scheduling

### Experimental Setup

The experiment evaluated three scheduling strategies for a skewed workload of 8,000 items using 10 physical CPU cores:

1. **Block Static:** Each process receives one contiguous block of items.
2. **Cyclic Static:** Items are distributed among processes in round-robin order.
3. **Dynamic Scheduling:** Workers obtain tasks from a shared queue using chunk sizes C = 1, 8, 64, and 512.

The workload per item was calculated using:

\[
K(i)=1+\left\lfloor(i/40)^2\right\rfloor
\]

Three runs were performed for each configuration. Median wall time and load imbalance were recorded.

### Results

| Scheduling strategy | Median wall time (s) | Imbalance λ |
|---|---:|---:|
| Block Static | 2.3824 | 2.4139 |
| Cyclic Static | 1.4952 | 1.0361 |
| Dynamic C = 1 | 1.5224 | 1.0059 |
| Dynamic C = 8 | 1.5693 | 1.0127 |
| Dynamic C = 64 | 1.6387 | 1.0789 |
| Dynamic C = 512 | 2.1180 | 1.6322 |

### Analysis

Block Static produced the slowest result (2.3824 s) and the highest load imbalance (λ = 2.4139). This happened because computationally expensive items were not distributed evenly among workers.

Cyclic Static significantly improved performance, reducing execution time to 1.4952 s and imbalance to 1.0361. Round-robin distribution spreads expensive items more evenly across processes.

For Dynamic Scheduling, C = 1 achieved the lowest execution time among dynamic configurations (1.5224 s) and the lowest imbalance (λ = 1.0059). However, it was slightly slower than Cyclic Static. Smaller chunks improve workload distribution but require more frequent synchronization with the shared queue.

As chunk size increased, execution time and imbalance also increased. In particular, C = 512 produced 2.1180 s and λ = 1.6322 because large chunks reduced scheduling flexibility and caused some workers to receive substantially more work than others.

### Conclusion

Cyclic Static was the fastest overall strategy in this experiment, while Dynamic C = 1 provided the best balance among dynamic configurations. The results demonstrate that workload distribution is important for parallel performance. A small chunk size improves load balancing, but synchronization overhead can prevent dynamic scheduling from outperforming a well-designed static strategy.

### Verification

```text
VERIFY_HASH[PHASE4]: AD3660028CE81090 (P_log=10)
```

---

## Verification Summary

```text
VERIFY_HASH[PHASE0]: 0A1B436D8B26AC19 (P_log=10)
VERIFY_HASH[PHASE1]: 536A918A59CA4ED4 (P_log=10)
VERIFY_HASH[PHASE2]: 42EDB09D9DE6B422 (P_log=10)
VERIFY_HASH[PHASE3]: E95E95D1DA76998D (P_log=10)
VERIFY_HASH[PHASE4]: AD3660028CE81090 (P_log=10)
```

---

## Appendix A — Complete Python Source Code

The following source files are included in this report. Keep the separate `.py` files in the project directory as well, because the scripts import `harness.py` as a module.

### `harness.py`

```python

from dataclasses import dataclass
import multiprocessing as mp
import time
from typing import Callable


@dataclass
class BenchStats:
    min_ms: float
    median_ms: float
    iqr_ms: float


def fnv1a_hash(s: str) -> int:
    h = 14695981039346656037

    for b in s.encode("utf-8"):
        h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF

    return h


def run_benchmark(
    fn: Callable[[], None],
    warmup: int = 2,
    runs: int = 7
) -> BenchStats:

    for _ in range(warmup):
        fn()

    samples = []

    for _ in range(runs):
        t0 = time.perf_counter_ns()
        fn()
        samples.append(
            (time.perf_counter_ns() - t0) / 1e6
        )

    samples.sort()

    med = samples[runs // 2]
    iqr = samples[(3 * runs) // 4] - samples[runs // 4]

    return BenchStats(
        min_ms=samples[0],
        median_ms=med,
        iqr_ms=iqr
    )


def emit_verify_tag(
    phase: str,
    seed: int,
    m1: float,
    m2: float
) -> str:

    hw = mp.cpu_count()

    sig = fnv1a_hash(
        f"{phase}|{seed}|{hw}|{m1:.4f}|{m2:.4f}"
    )

    return (
        f"VERIFY_HASH[{phase}]: "
        f"{sig:016X} (P_log={hw})"
    )
```

### `task0_cal.py`

```python

import time
import multiprocessing as mp

from harness import emit_verify_tag


STUDENT_ID = 230103360
NUM_CALLS = 1_000_000


def measure_clock_latency():
    start = time.perf_counter_ns()

    for _ in range(NUM_CALLS):
        time.perf_counter_ns()

    end = time.perf_counter_ns()

    total_ns = end - start
    average_ns = total_ns / NUM_CALLS

    return average_ns, total_ns


if __name__ == "__main__":

    print("PHASE 0: Hardware Calibration")
    print("-" * 40)

    average_ns, total_ns = measure_clock_latency()

    print(f"Student ID: {STUDENT_ID}")
    print(f"CPU Count: {mp.cpu_count()}")
    print(f"Number of calls: {NUM_CALLS}")
    print(f"Total time: {total_ns / 1e6:.4f} ms")
    print(f"Average call latency: {average_ns:.4f} ns")

    verify = emit_verify_tag(
        "PHASE0",
        STUDENT_ID,
        average_ns,
        total_ns / 1e6
    )

    print("\n" + verify)
```

### `task1_falsesharing.py`

```python

import multiprocessing as mp
from multiprocessing import shared_memory
import ctypes
import time
import statistics

from harness import emit_verify_tag


STUDENT_ID = 230103360
M = 16_000_000
P_PHYS = 10
P_LOG = mp.cpu_count()

STRIDES = [1, 2, 4, 8, 16, 32]
PROCESS_COUNTS = sorted(set([1, 2, 4, 8, P_LOG]))

RUNS = 3
MASK = 0xFFFFFFFFFFFFFFFF
MULTIPLIER = 6364136223846793005


# Worker function
def fs_worker(shm_name, slot_idx, iters):

    shm = shared_memory.SharedMemory(name=shm_name)
    arr = (ctypes.c_uint64 * 512).from_buffer(shm.buf)

    acc = arr[slot_idx]

    for i in range(iters):
        acc = (
            acc * MULTIPLIER + (i | 1)
        ) & MASK

        arr[slot_idx] = acc

    del arr
    shm.close()


# One parallel execution
def execute_test(p, stride):

    shm = shared_memory.SharedMemory(create=True, size=4096)

    processes = []

    try:
        arr = (ctypes.c_uint64 * 512).from_buffer(shm.buf)

        for i in range(512):
            arr[i] = 0

        del arr

        base_iters = M // p
        remainder = M % p

        start = time.perf_counter_ns()

        for worker_id in range(p):

            iters = base_iters + (1 if worker_id < remainder else 0)
            slot_idx = worker_id * stride

            process = mp.Process(
                target=fs_worker,
                args=(shm.name, slot_idx, iters)
            )

            processes.append(process)
            process.start()

        for process in processes:
            process.join()

            if process.exitcode != 0:
                raise RuntimeError(
                    f"Worker failed: exit code {process.exitcode}"
                )

        end = time.perf_counter_ns()

        return (end - start) / 1e6

    finally:
        shm.close()
        shm.unlink()


# Benchmark with repeated measurements
def benchmark(p, stride):

    samples = []

    for run in range(RUNS):
        elapsed = execute_test(p, stride)
        samples.append(elapsed)

        print(
            f"  Run {run + 1}/{RUNS}: {elapsed:.2f} ms"
        )

    samples.sort()

    median = statistics.median(samples)
    quartiles = statistics.quantiles(
        samples, n=4, method="inclusive"
    )
    iqr = quartiles[2] - quartiles[0]

    throughput = M / (median / 1000) / 1e6

    return median, iqr, throughput


# Karp-Flatt serial fraction
def karp_flatt(speedup, p):

    if p <= 1:
        return None

    return (
        (1 / speedup) - (1 / p)
    ) / (1 - (1 / p))


if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 1: FALSE SHARING")
    print("=" * 60)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Physical cores: {P_PHYS}")
    print(f"Logical threads: {P_LOG}")
    print(f"Total operations: {M:,}")

    # PART 1: STRIDE SWEEP

    print("\nPART 1: STRIDE SWEEP")
    stride_results = {}

    for stride in STRIDES:

        print(f"\nTesting stride = {stride}")

        median, iqr, throughput = benchmark(
            P_PHYS, stride
        )

        stride_results[stride] = median

        print(f"Median: {median:.2f} ms")
        print(f"IQR: {iqr:.2f} ms")
        print(f"Throughput: {throughput:.4f} Mops/s")

    # PART 2: PROCESS SCALING

    print("\n" + "=" * 60)
    print("PART 2: PROCESS SCALING")
    print("=" * 60)

    scaling_results = {}

    for stride in [1, 16]:

        print(f"\nScaling test: stride = {stride}")

        scaling_results[stride] = {}

        for p in PROCESS_COUNTS:

            print(f"\nProcesses: {p}")

            median, iqr, throughput = benchmark(
                p, stride
            )

            scaling_results[stride][p] = median

            print(f"Median: {median:.2f} ms")
            print(f"IQR: {iqr:.2f} ms")
            print(f"Throughput: {throughput:.4f} Mops/s")

    # PART 3: SPEEDUP, EFFICIENCY, KAR​​P-FLATT

    print("\n" + "=" * 60)
    print("PART 3: SCALING ANALYSIS")
    print("=" * 60)

    for stride in [1, 16]:

        print(f"\nStride = {stride}")

        t1 = scaling_results[stride][1]

        print(
            f"{'p':>5} {'Time(ms)':>12} "
            f"{'Speedup':>12} {'Efficiency':>12} "
            f"{'Karp-Flatt':>12}"
        )

        for p in PROCESS_COUNTS:

            tp = scaling_results[stride][p]

            speedup = t1 / tp
            efficiency = speedup / p
            e = karp_flatt(speedup, p)

            e_text = f"{e:.5f}" if e is not None else "N/A"

            print(
                f"{p:>5} {tp:>12.2f} "
                f"{speedup:>12.4f} "
                f"{efficiency:>12.4f} "
                f"{e_text:>12}"
            )

    # PART 4: VERIFICATION HASH

    median_stride1 = stride_results[1]
    median_stride16 = stride_results[16]

    verify = emit_verify_tag(
        "PHASE1",
        STUDENT_ID,
        median_stride1,
        median_stride16
    )

    print("\n" + "=" * 60)
    print(verify)
    print("=" * 60)
```

### `task2_scaling.py`

```python

import multiprocessing as mp
import math
import time
import statistics

from harness import emit_verify_tag


STUDENT_ID = 230103360

P_LOG = mp.cpu_count()
P_PHYS = 10

N_STRONG = 1_200_000
N0_WEAK = 200_000

RUNS = 3
CHUNK_MULTIPLIER = 4


# Stage A: serial computation in the parent process
def stage_a(n):

    total = 0.0

    for i in range(n):
        x = (i + 1) * 0.0001

        for _ in range(5):
            x = math.sin(x)
            x = math.sqrt(abs(x) + 1.0)

        total += x

    return total


# Stage B: parallel worker
def stage_b_worker(task):

    start, end = task
    total = 0.0

    for i in range(start, end):

        x = (i + 1) * 0.0001

        for _ in range(10):
            x = math.sin(x)
            x = math.sqrt(abs(x) + 1.0)
            x = math.fma(x, 1.000001, 0.000001)

        total += x

    return total


# Divide elements into chunks
def create_chunks(n, p):

    chunk_count = p * CHUNK_MULTIPLIER
    chunks = []

    for i in range(chunk_count):

        start = (n * i) // chunk_count
        end = (n * (i + 1)) // chunk_count

        if start < end:
            chunks.append((start, end))

    return chunks


# One complete pipeline trial
def run_pipeline(pool, n, p):

    stage_a_n = int(0.05 * n)

    # Stage A: serial
    a_start = time.perf_counter_ns()
    result_a = stage_a(stage_a_n)
    a_end = time.perf_counter_ns()

    stage_a_ms = (a_end - a_start) / 1e6

    # Stage B: parallel
    chunks = create_chunks(n, p)

    b_start = time.perf_counter_ns()
    results = pool.map(stage_b_worker, chunks)
    b_end = time.perf_counter_ns()

    stage_b_ms = (b_end - b_start) / 1e6

    # Keep computed results
    checksum = result_a + sum(results)

    total_ms = stage_a_ms + stage_b_ms

    return total_ms, stage_a_ms, stage_b_ms, checksum


# Benchmark with persistent pool
def benchmark(p, n):

    total_samples = []
    stage_a_samples = []
    stage_b_samples = []

    with mp.Pool(processes=p) as pool:

        for run in range(RUNS):

            total, a_time, b_time, checksum = run_pipeline(
                pool, n, p
            )

            total_samples.append(total)
            stage_a_samples.append(a_time)
            stage_b_samples.append(b_time)

            print(
                f"  Run {run + 1}/{RUNS}: "
                f"Total={total:.2f} ms | "
                f"Stage A={a_time:.2f} ms | "
                f"Stage B={b_time:.2f} ms"
            )

    return (
        statistics.median(total_samples),
        statistics.median(stage_a_samples),
        statistics.median(stage_b_samples)
    )


if __name__ == "__main__":

    print("=" * 65)
    print("PHASE 2: STRONG SCALING VS WEAK SCALING")
    print("=" * 65)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Logical CPUs: {P_LOG}")
    print(f"Physical cores: {P_PHYS}")
    print(f"Strong workload: {N_STRONG:,}")
    print(f"Weak workload per process: {N0_WEAK:,}")

    process_counts = list(range(1, P_LOG + 2))

    # ==========================================
    # PART 1: STRONG SCALING
    # ==========================================

    print("\n" + "=" * 65)
    print("PART 1: STRONG SCALING")
    print("=" * 65)

    strong_results = {}

    for p in process_counts:

        print(f"\nProcesses: {p}")

        total, stage_a_ms, stage_b_ms = benchmark(
            p, N_STRONG
        )

        strong_results[p] = {
            "total": total,
            "stage_a": stage_a_ms,
            "stage_b": stage_b_ms
        }

    t1_strong = strong_results[1]["total"]

    s = strong_results[1]["stage_a"] / t1_strong
    amdahl_cap = 1 / s if s > 0 else float("inf")

    print("\nSTRONG SCALING SUMMARY")
    print(
        f"{'p':>5} {'Time(ms)':>12} "
        f"{'Speedup':>12} {'Efficiency':>12}"
    )

    for p in process_counts:

        tp = strong_results[p]["total"]

        speedup = t1_strong / tp
        efficiency = speedup / p

        print(
            f"{p:>5} {tp:>12.2f} "
            f"{speedup:>12.4f} {efficiency:>12.4f}"
        )

    print(f"\nSerial fraction s: {s:.6f}")
    print(f"Amdahl theoretical cap: {amdahl_cap:.4f}")

    # ==========================================
    # PART 2: WEAK SCALING
    # ==========================================

    print("\n" + "=" * 65)
    print("PART 2: WEAK SCALING")
    print("=" * 65)

    weak_results = {}

    for p in process_counts:

        n = p * N0_WEAK

        print(f"\nProcesses: {p}")
        print(f"Total elements: {n:,}")

        total, stage_a_ms, stage_b_ms = benchmark(
            p, n
        )

        weak_results[p] = {
            "total": total,
            "stage_a": stage_a_ms,
            "stage_b": stage_b_ms
        }

    t1_weak = weak_results[1]["total"]

    print("\nWEAK SCALING SUMMARY")
    print(
        f"{'p':>5} {'N':>12} {'Time(ms)':>12} "
        f"{'Weak Eff.':>12} {'Gustafson':>12}"
    )

    for p in process_counts:

        n = p * N0_WEAK

        tp = weak_results[p]["total"]
        stage_a_ms = weak_results[p]["stage_a"]

        weak_efficiency = t1_weak / tp

        alpha = stage_a_ms / tp

        gustafson = p - alpha * (p - 1)

        print(
            f"{p:>5} {n:>12,} {tp:>12.2f} "
            f"{weak_efficiency:>12.4f} "
            f"{gustafson:>12.4f}"
        )

    # ==========================================
    # PART 3: ARCHITECTURAL INFLECTION
    # ==========================================

    print("\n" + "=" * 65)
    print("PART 3: ARCHITECTURAL INFLECTION")
    print("=" * 65)

    t_phys = strong_results[P_PHYS]["total"]
    t_next = strong_results[P_PHYS + 1]["total"]

    marginal_speedup = t_phys / t_next
    marginal_gain = (marginal_speedup - 1) * 100

    print(f"Time at Pphys={P_PHYS}: {t_phys:.2f} ms")
    print(f"Time at Pphys+1={P_PHYS + 1}: {t_next:.2f} ms")
    print(f"Marginal speedup: {marginal_speedup:.4f}")
    print(f"Marginal gain: {marginal_gain:.2f}%")

    # ==========================================
    # PART 4: VERIFICATION HASH
    # ==========================================

    strong_speedup = (
        t1_strong / strong_results[P_LOG]["total"]
    )

    weak_gustafson = (
        P_LOG
        - (
            weak_results[P_LOG]["stage_a"]
            / weak_results[P_LOG]["total"]
        ) * (P_LOG - 1)
    )

    verify = emit_verify_tag(
        "PHASE2",
        STUDENT_ID,
        strong_speedup,
        weak_gustafson
    )

    print("\n" + "=" * 65)
    print(verify)
    print("=" * 65)
```

### `task3_roofline_gemm.py`

```python

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
```

### `task4_scheduling.py`

```python

import multiprocessing as mp
import time
import math
import statistics

from harness import emit_verify_tag


STUDENT_ID = 230103360

N = 8000
P_PHYS = 10
CHUNK_SIZES = [1, 8, 64, 512]


# ==================================================
# WORKLOAD
# ==================================================

def calculate_work(item):

    k = 1 + (item * item // 1600)

    x = (item + 1) * 0.001

    for _ in range(k):
        x = math.sin(x)
        x = math.cos(x)
        x = math.sqrt(abs(x) + 1.0)

    return x


# ==================================================
# STATIC WORKER
# ==================================================

def static_worker(worker_id, p, mode, worker_times):

    start = time.perf_counter()

    result = 0.0

    if mode == "block":

        block_size = (N + p - 1) // p

        first = worker_id * block_size
        last = min(first + block_size, N)

        for item in range(first, last):
            result += calculate_work(item)

    elif mode == "cyclic":

        for item in range(worker_id, N, p):
            result += calculate_work(item)

    worker_times[worker_id] = (
        time.perf_counter() - start
    )

    return result


# ==================================================
# DYNAMIC QUEUE WORKER
# ==================================================

def dynamic_worker(
    worker_id,
    p,
    chunk_size,
    counter,
    worker_times
):

    start = time.perf_counter()

    result = 0.0

    while True:

        # Get next chunk from shared queue
        with counter.get_lock():

            first = counter.value

            counter.value += chunk_size

        if first >= N:
            break

        last = min(first + chunk_size, N)

        for item in range(first, last):

            result += calculate_work(item)

    worker_times[worker_id] = (
        time.perf_counter() - start
    )

    return result


# ==================================================
# RUN STATIC STRATEGY
# ==================================================

def run_static(mode):

    worker_times = mp.Array("d", P_PHYS)

    processes = []

    start = time.perf_counter()

    for worker_id in range(P_PHYS):

        process = mp.Process(
            target=static_worker,
            args=(
                worker_id,
                P_PHYS,
                mode,
                worker_times
            )
        )

        processes.append(process)
        process.start()

    for process in processes:

        process.join()

        if process.exitcode != 0:
            raise RuntimeError(
                f"Static worker failed: {process.exitcode}"
            )

    wall_time = time.perf_counter() - start

    times = list(worker_times)

    return wall_time, times


# ==================================================
# RUN DYNAMIC STRATEGY
# ==================================================

def run_dynamic(chunk_size):

    counter = mp.Value("i", 0)

    worker_times = mp.Array("d", P_PHYS)

    processes = []

    start = time.perf_counter()

    for worker_id in range(P_PHYS):

        process = mp.Process(
            target=dynamic_worker,
            args=(
                worker_id,
                P_PHYS,
                chunk_size,
                counter,
                worker_times
            )
        )

        processes.append(process)
        process.start()

    for process in processes:

        process.join()

        if process.exitcode != 0:
            raise RuntimeError(
                f"Dynamic worker failed: {process.exitcode}"
            )

    wall_time = time.perf_counter() - start

    times = list(worker_times)

    return wall_time, times


# ==================================================
# LOAD IMBALANCE
# ==================================================

def calculate_imbalance(worker_times):

    average = statistics.mean(worker_times)

    if average == 0:
        return 0.0

    return max(worker_times) / average


# ==================================================
# BENCHMARK
# ==================================================

def benchmark_static(mode, runs=3):

    wall_samples = []
    imbalance_samples = []

    for run in range(runs):

        wall, times = run_static(mode)

        imbalance = calculate_imbalance(times)

        wall_samples.append(wall)
        imbalance_samples.append(imbalance)

        print(
            f"Run {run + 1}: "
            f"Wall={wall:.4f} s | "
            f"Lambda={imbalance:.4f}"
        )

    return (
        statistics.median(wall_samples),
        statistics.median(imbalance_samples)
    )


def benchmark_dynamic(chunk_size, runs=3):

    wall_samples = []
    imbalance_samples = []

    for run in range(runs):

        wall, times = run_dynamic(chunk_size)

        imbalance = calculate_imbalance(times)

        wall_samples.append(wall)
        imbalance_samples.append(imbalance)

        print(
            f"Run {run + 1}: "
            f"Wall={wall:.4f} s | "
            f"Lambda={imbalance:.4f}"
        )

    return (
        statistics.median(wall_samples),
        statistics.median(imbalance_samples)
    )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    mp.freeze_support()

    print("=" * 65)
    print("PHASE 4: SKEWED WORKLOADS & DYNAMIC CHUNK QUEUE")
    print("=" * 65)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Total items: {N}")
    print(f"Physical cores: {P_PHYS}")

    # ==========================================
    # PART 1: STATIC BLOCK
    # ==========================================

    print("\nPART 1: CONTIGUOUS BLOCK STATIC")

    block_wall, block_lambda = benchmark_static("block")

    print(f"\nMedian wall time: {block_wall:.4f} s")
    print(f"Median imbalance: {block_lambda:.4f}")

    # ==========================================
    # PART 2: CYCLIC STATIC
    # ==========================================

    print("\nPART 2: CYCLIC ROUND-ROBIN STATIC")

    cyclic_wall, cyclic_lambda = benchmark_static("cyclic")

    print(f"\nMedian wall time: {cyclic_wall:.4f} s")
    print(f"Median imbalance: {cyclic_lambda:.4f}")

    # ==========================================
    # PART 3: DYNAMIC QUEUE
    # ==========================================

    print("\nPART 3: DYNAMIC QUEUE")

    dynamic_results = {}

    for chunk in CHUNK_SIZES:

        print(f"\nTesting chunk size C = {chunk}")

        wall, imbalance = benchmark_dynamic(chunk)

        dynamic_results[chunk] = {
            "wall": wall,
            "lambda": imbalance
        }

        print(f"Median wall time: {wall:.4f} s")
        print(f"Median imbalance: {imbalance:.4f}")

    # ==========================================
    # PART 4: SELECT OPTIMAL CHUNK
    # ==========================================

    best_chunk = min(
        dynamic_results,
        key=lambda c: dynamic_results[c]["wall"]
    )

    best_wall = dynamic_results[best_chunk]["wall"]

    best_lambda = dynamic_results[best_chunk]["lambda"]

    print("\n" + "=" * 65)
    print("SCHEDULING SUMMARY")
    print("=" * 65)

    print(
        f"{'Strategy':<25} {'Wall (s)':>12} "
        f"{'Lambda':>12}"
    )

    print(
        f"{'Block Static':<25} "
        f"{block_wall:>12.4f} "
        f"{block_lambda:>12.4f}"
    )

    print(
        f"{'Cyclic Static':<25} "
        f"{cyclic_wall:>12.4f} "
        f"{cyclic_lambda:>12.4f}"
    )

    for chunk in CHUNK_SIZES:

        result = dynamic_results[chunk]

        print(
            f"{'Dynamic C=' + str(chunk):<25} "
            f"{result['wall']:>12.4f} "
            f"{result['lambda']:>12.4f}"
        )

    print(f"\nOptimal chunk size: {best_chunk}")

    print(f"Best dynamic wall time: {best_wall:.4f} s")

    # ==========================================
    # VERIFICATION HASH
    # ==========================================

    verify = emit_verify_tag(
        "PHASE4",
        STUDENT_ID,
        block_wall * 1000,
        best_wall * 1000
    )

    print("\n" + "=" * 65)
    print(verify)
    print("=" * 65)
```

---

**End of Report**
