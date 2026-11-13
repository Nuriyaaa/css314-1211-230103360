
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
