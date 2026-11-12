
import multiprocessing as mp
from multiprocessing import shared_memory
import time
import statistics


STUDENT_ID = 230103360
P_PHYS = 10

BUFFER_SIZE = 96 * 1_000_000  # 96 MB per buffer
FLOPS_PER_WORKER = 80_000_000

REPEATS = 5


# -------------------------------------------------
# PART 1: DRAM STREAMING BANDWIDTH
# -------------------------------------------------

def memory_copy_worker(shm_a_name, shm_b_name, start, end, ready):
    """Copy a partition of shared memory from B to A."""

    shm_a = shared_memory.SharedMemory(name=shm_a_name)
    shm_b = shared_memory.SharedMemory(name=shm_b_name)

    try:
        mv_a = shm_a.buf
        mv_b = shm_b.buf

        ready.wait()

        mv_a[start:end] = mv_b[start:end]

        mv_a.release()
        mv_b.release()

    finally:
        shm_a.close()
        shm_b.close()


def run_bandwidth_trial():
    """Measure parallel shared-memory copy bandwidth."""

    shm_a = shared_memory.SharedMemory(
        create=True, size=BUFFER_SIZE
    )

    shm_b = shared_memory.SharedMemory(
        create=True, size=BUFFER_SIZE
    )

    try:
        # Initialize source buffer before timing.
        # Initialize source buffer in 1 MB chunks.
        view = shm_b.buf.cast("B")
        chunk = bytes([1]) * (1024 * 1024)

        for offset in range(0, BUFFER_SIZE, len(chunk)):
            end = min(offset + len(chunk), BUFFER_SIZE)
            view[offset:end] = chunk[:end - offset]

        view.release()

        ready = mp.Event()
        processes = []

        for worker in range(P_PHYS):
            start = worker * BUFFER_SIZE // P_PHYS
            end = (worker + 1) * BUFFER_SIZE // P_PHYS

            process = mp.Process(
                target=memory_copy_worker,
                args=(
                    shm_a.name,
                    shm_b.name,
                    start,
                    end,
                    ready
                )
            )

            processes.append(process)

        for process in processes:
            process.start()

        # Workers are created before the timed region.
        start_time = time.perf_counter_ns()
        ready.set()

        for process in processes:
            process.join()

        end_time = time.perf_counter_ns()

        for process in processes:
            if process.exitcode != 0:
                raise RuntimeError(
                    f"Memory worker failed: {process.exitcode}"
                )

        return (end_time - start_time) / 1e9

    finally:
        shm_a.close()
        shm_a.unlink()

        shm_b.close()
        shm_b.unlink()


# -------------------------------------------------
# PART 2: PYTHON COMPUTE CEILING
# -------------------------------------------------

def compute_worker(iterations, ready):
    """
    Execute 16 independent scalar multiply-add chains.
    Each update represents approximately 2 FLOPs.
    """

    a = 1.0000001
    b = 0.0000001

    x0 = 1.0
    x1 = 1.1
    x2 = 1.2
    x3 = 1.3
    x4 = 1.4
    x5 = 1.5
    x6 = 1.6
    x7 = 1.7
    x8 = 1.8
    x9 = 1.9
    x10 = 2.0
    x11 = 2.1
    x12 = 2.2
    x13 = 2.3
    x14 = 2.4
    x15 = 2.5

    ready.wait()

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

    return x0 + x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11 + x12 + x13 + x14 + x15


def run_compute_trial():
    """Measure parallel Python scalar computation."""

    iterations = FLOPS_PER_WORKER // 32

    ready = mp.Event()
    processes = []

    for _ in range(P_PHYS):
        process = mp.Process(
            target=compute_worker,
            args=(iterations, ready)
        )

        processes.append(process)

    for process in processes:
        process.start()

    start_time = time.perf_counter_ns()
    ready.set()

    for process in processes:
        process.join()

    end_time = time.perf_counter_ns()

    for process in processes:
        if process.exitcode != 0:
            raise RuntimeError(
                f"Compute worker failed: {process.exitcode}"
            )

    return (end_time - start_time) / 1e9


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    print("=" * 70)
    print("PHASE 3A: EMPIRICAL MACHINE ROOFLINE")
    print("=" * 70)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Physical cores: {P_PHYS}")
    print(f"Buffer size: {BUFFER_SIZE / 1e6:.0f} MB each")
    print(f"Compute FLOPs per worker: {FLOPS_PER_WORKER:,}")

    # DRAM Bandwidth

    print("\n1. DRAM STREAMING BANDWIDTH")
    print("-" * 70)

    bandwidth_times = []

    for trial in range(REPEATS):
        elapsed = run_bandwidth_trial()
        bandwidth_times.append(elapsed)

        print(
            f"Trial {trial + 1}: "
            f"{elapsed * 1000:.3f} ms"
        )

    median_bandwidth_time = statistics.median(
        bandwidth_times
    )

    bandwidth_gbs = (
        2 * BUFFER_SIZE
        / (median_bandwidth_time * 1e9)
    )

    print(f"Median time: {median_bandwidth_time * 1000:.3f} ms")
    print(f"Sustained bandwidth: {bandwidth_gbs:.4f} GB/s")

    # Compute Ceiling

    print("\n2. PYTHON COMPUTE CEILING")
    print("-" * 70)

    compute_times = []

    for trial in range(REPEATS):
        elapsed = run_compute_trial()
        compute_times.append(elapsed)

        print(
            f"Trial {trial + 1}: "
            f"{elapsed * 1000:.3f} ms"
        )

    median_compute_time = statistics.median(
        compute_times
    )

    total_flops = FLOPS_PER_WORKER * P_PHYS

    compute_gflops = (
        total_flops / median_compute_time / 1e9
    )

    print(f"Median time: {median_compute_time * 1000:.3f} ms")
    print(f"Total FLOPs: {total_flops:,}")
    print(f"Sustained compute: {compute_gflops:.6f} GFLOP/s")

    # Ridge Point

    ridge_point = compute_gflops / bandwidth_gbs

    print("\n3. EMPIRICAL RIDGE POINT")
    print("-" * 70)

    print(f"Compute ceiling: {compute_gflops:.6f} GFLOP/s")
    print(f"Memory bandwidth: {bandwidth_gbs:.4f} GB/s")
    print(f"Ridge point: {ridge_point:.6f} FLOPs/Byte")

    print("\nPHASE 3A COMPLETED")


if __name__ == "__main__":
    mp.freeze_support()
    main()
