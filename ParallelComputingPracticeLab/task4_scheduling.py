
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
