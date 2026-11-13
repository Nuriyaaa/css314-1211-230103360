
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
