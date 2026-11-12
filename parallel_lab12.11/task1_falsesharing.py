
import ctypes
import multiprocessing as mp
from multiprocessing import shared_memory
import time

from harness import run_benchmark, emit_verify_tag


STUDENT_ID = 230103360
TOTAL_OPERATIONS = 24_000_000
STRIDES = [1, 2, 4, 8, 16, 32]


def fs_worker(shm_name, slot_idx, iters):
    """Worker that updates one shared-memory slot."""
    shm = shared_memory.SharedMemory(name=shm_name)

    try:
        arr = (ctypes.c_uint64 * 512).from_buffer(shm.buf)

        acc = arr[slot_idx]
        mask = 0xFFFFFFFFFFFFFFFF
        mult = 6364136223846793005

        for i in range(iters):
            acc = (acc * mult + (i | 1)) & mask
            arr[slot_idx] = acc

        del arr

    finally:
        shm.close()


def run_false_sharing(p, stride):
    """Run one false-sharing experiment."""
    shm = shared_memory.SharedMemory(create=True, size=4096)

    try:
        processes = []

        for worker_id in range(p):
            slot_idx = worker_id * stride

            process = mp.Process(
                target=fs_worker,
                args=(
                    shm.name,
                    slot_idx,
                    TOTAL_OPERATIONS // p
                )
            )

            processes.append(process)

        start = time.perf_counter_ns()

        for process in processes:
            process.start()

        for process in processes:
            process.join()

        end = time.perf_counter_ns()

        for process in processes:
            if process.exitcode != 0:
                raise RuntimeError(
                    f"Worker failed: exit code {process.exitcode}"
                )

        return (end - start) / 1e6

    finally:
        shm.close()
        shm.unlink()


def main():
    print("=" * 65)
    print("PHASE 1: FALSE SHARING AND CACHE-LINE CONTENTION")
    print("=" * 65)

    p_phys = 10
    p_log = mp.cpu_count()

    # Experiment 1A: stride sensitivity
    print("\nTABLE 1A: STRIDE SENSITIVITY")
    print(f"Processes: {p_phys}")
    print("-" * 65)

    stride_results = {}

    for stride in STRIDES:
        stats = run_benchmark(
            lambda s=stride: run_false_sharing(p_phys, s),
            warmup_runs=2,
            timed_runs=7
        )

        throughput = TOTAL_OPERATIONS / (
            stats.median_ms * 1000
        )

        stride_results[stride] = stats.median_ms

        print(
            f"Stride={stride:2d} | "
            f"Median={stats.median_ms:10.3f} ms | "
            f"IQR={stats.iqr_ms:10.3f} ms | "
            f"Throughput={throughput:10.3f} Mops/s"
        )

    # Experiment 1B: process scaling
    print("\nTABLE 1B: PROCESS SCALING")
    print("-" * 65)

    process_counts = [
        p for p in [1, 2, 4, 8, 10]
        if p <= p_log
    ]

    scaling_results = {}

    for stride in [1, 16]:
        print(f"\nStride = {stride}")

        times = {}

        for p in process_counts:
            stats = run_benchmark(
                lambda p=p, s=stride: run_false_sharing(p, s),
                warmup_runs=2,
                timed_runs=7
            )

            times[p] = stats.median_ms

        t1 = times[1]

        for p in process_counts:
            tp = times[p]
            speedup = t1 / tp
            efficiency = speedup / p

            if p >= 2:
                karp_flatt = (
                    (1 / speedup) - (1 / p)
                ) / (1 - (1 / p))
            else:
                karp_flatt = None

            print(
                f"p={p:2d} | "
                f"Time={tp:10.3f} ms | "
                f"Speedup={speedup:8.3f} | "
                f"Efficiency={efficiency:8.3f} | "
                f"Karp-Flatt={karp_flatt if karp_flatt is not None else 'N/A'}"
            )

        scaling_results[stride] = times

    # Phase 1 verification
    hash_line = emit_verify_tag(
        "PHASE1",
        STUDENT_ID,
        stride_results[1],
        stride_results[16]
    )

    print("\n" + hash_line)


if __name__ == "__main__":
    mp.freeze_support()
    main()
