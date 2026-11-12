
import multiprocessing as mp
import math
import time
import statistics

from harness import run_benchmark, emit_verify_tag


STUDENT_ID = 230103360

STRONG_N = 1_600_000
WEAK_N0 = 250_000

WARMUP_RUNS = 2
TIMED_RUNS = 5

P_LOG = mp.cpu_count()


def serial_stage_a(n):
    """
    Serial reduction and prefix filter.
    Processes the first 5% of elements.
    Performs 12 transcendental operations per element.
    """
    count = max(1, int(n * 0.05))
    result = 0.0

    for i in range(count):
        x = (i + 1) * 0.000001

        for _ in range(6):
            x = math.sin(x)
            x = math.sqrt(abs(x) + 1.0)

        result += x

    return result


def compute_chunk(args):
    """
    Parallel Stage B.
    Each element executes 35 multiply-add and
    trigonometric iterations.
    """
    start, end = args
    result = 0.0

    for i in range(start, end):
        x = (i + 1) * 0.000001

        for j in range(35):
            x = math.sin(x * 1.0000001 + (j + 1) * 0.00000001)

        result += x

    return result


def make_chunks(n, p):
    """Divide N elements into p nearly equal chunks."""
    chunks = []

    for worker in range(p):
        start = worker * n // p
        end = (worker + 1) * n // p
        chunks.append((start, end))

    return chunks


def run_trial(pool, n, p):
    """Execute serial and parallel stages."""
    stage_a_start = time.perf_counter_ns()

    serial_result = serial_stage_a(n)

    stage_a_end = time.perf_counter_ns()

    stage_a_ms = (stage_a_end - stage_a_start) / 1e6

    chunks = make_chunks(n, p)

    parallel_results = pool.map(compute_chunk, chunks)

    checksum = serial_result + sum(parallel_results)

    return stage_a_ms, checksum


def benchmark_configuration(n, p):
    """
    Create a persistent pool outside the timed region.
    Benchmark only the computation and pool.map operation.
    """
    stage_a_samples = []

    with mp.Pool(processes=p) as pool:

        def benchmark_function():
            stage_a_ms, _ = run_trial(pool, n, p)
            stage_a_samples.append(stage_a_ms)

        stats = run_benchmark(
            benchmark_function,
            warmup_runs=WARMUP_RUNS,
            timed_runs=TIMED_RUNS
        )

    median_stage_a = statistics.median(
        stage_a_samples[WARMUP_RUNS:]
    )

    return stats, median_stage_a


def main():

    print("=" * 75)
    print("PHASE 2: STRONG SCALING AND WEAK SCALING")
    print("=" * 75)

    print(f"Student ID: {STUDENT_ID}")
    print(f"Logical processors: {P_LOG}")
    print(f"Strong workload: {STRONG_N:,}")
    print(f"Weak workload per process: {WEAK_N0:,}")

    process_counts = range(1, P_LOG + 1)

    # -------------------------------------------------
    # EXPERIMENT 2A: STRONG SCALING
    # -------------------------------------------------

    print("\nEXPERIMENT 2A: STRONG SCALING")
    print("-" * 75)

    strong_results = {}

    for p in process_counts:

        stats, stage_a_ms = benchmark_configuration(
            STRONG_N, p
        )

        strong_results[p] = stats.median_ms

        print(
            f"p={p:2d} | "
            f"Median={stats.median_ms:10.3f} ms | "
            f"IQR={stats.iqr_ms:10.3f} ms | "
            f"Min={stats.min_ms:10.3f} ms | "
            f"Max={stats.max_ms:10.3f} ms"
        )

    strong_t1 = strong_results[1]

    print("\nSTRONG SCALING SPEEDUP AND EFFICIENCY")
    print("-" * 75)

    for p in process_counts:

        tp = strong_results[p]
        speedup = strong_t1 / tp
        efficiency = speedup / p

        print(
            f"p={p:2d} | "
            f"Speedup={speedup:8.4f} | "
            f"Efficiency={efficiency:8.4f}"
        )

    # -------------------------------------------------
    # EXPERIMENT 2B: WEAK SCALING
    # -------------------------------------------------

    print("\nEXPERIMENT 2B: WEAK SCALING")
    print("-" * 75)

    weak_results = {}
    stage_a_results = {}

    for p in process_counts:

        n = p * WEAK_N0

        stats, stage_a_ms = benchmark_configuration(n, p)

        weak_results[p] = stats.median_ms
        stage_a_results[p] = stage_a_ms

        print(
            f"p={p:2d} | "
            f"N={n:10,} | "
            f"Median={stats.median_ms:10.3f} ms | "
            f"Stage A={stage_a_ms:10.3f} ms | "
            f"IQR={stats.iqr_ms:10.3f} ms"
        )

    weak_t1 = weak_results[1]

    print("\nWEAK SCALING EFFICIENCY AND GUSTAFSON SPEEDUP")
    print("-" * 75)

    gustafson_results = {}

    for p in process_counts:

        tp = weak_results[p]

        weak_efficiency = weak_t1 / tp

        alpha = stage_a_results[p] / tp

        gustafson_speedup = p - alpha * (p - 1)

        gustafson_results[p] = gustafson_speedup

        print(
            f"p={p:2d} | "
            f"Weak Efficiency={weak_efficiency:8.4f} | "
            f"Alpha={alpha:8.4f} | "
            f"Gustafson Speedup={gustafson_speedup:8.4f}"
        )

    # -------------------------------------------------
    # AMDAHL'S LAW
    # -------------------------------------------------

    serial_fraction = (
        serial_stage_a(STRONG_N)
    )

    # Measure Stage A separately for strong workload.
    strong_stage_a_samples = []

    for _ in range(5):
        start = time.perf_counter_ns()
        serial_stage_a(STRONG_N)
        end = time.perf_counter_ns()

        strong_stage_a_samples.append(
            (end - start) / 1e6
        )

    stage_a_strong_ms = statistics.median(
        strong_stage_a_samples
    )

    s = stage_a_strong_ms / strong_t1

    theoretical_max = 1 / s if s > 0 else float("inf")

    theoretical_at_plog = (
        1 / (s + (1 - s) / P_LOG)
        if s > 0 else float("inf")
    )

    observed_at_plog = strong_t1 / strong_results[P_LOG]

    print("\nAMDAHL'S LAW ANALYSIS")
    print("-" * 75)

    print(f"Serial Stage A time: {stage_a_strong_ms:.4f} ms")
    print(f"Strong T1: {strong_t1:.4f} ms")
    print(f"Serial fraction: {s:.6f}")
    print(f"Theoretical maximum speedup: {theoretical_max:.4f}")
    print(f"Theoretical speedup at p={P_LOG}: {theoretical_at_plog:.4f}")
    print(f"Observed speedup at p={P_LOG}: {observed_at_plog:.4f}")

    # -------------------------------------------------
    # MARGINAL SPEEDUP ANALYSIS
    # -------------------------------------------------

    print("\nMARGINAL SPEEDUP ANALYSIS")
    print("-" * 75)

    previous_gain = None
    previous_speedup = 1.0

    for p in range(2, P_LOG + 1):

        current_speedup = strong_t1 / strong_results[p]
        marginal_gain = current_speedup - previous_speedup

        if previous_gain is not None and previous_gain != 0:
            drop = (
                (previous_gain - marginal_gain)
                / previous_gain
            ) * 100
        else:
            drop = None

        print(
            f"p={p:2d} | "
            f"Speedup={current_speedup:.4f} | "
            f"Marginal gain={marginal_gain:.4f} | "
            f"Drop={drop if drop is not None else 'N/A'}"
        )

        previous_gain = marginal_gain
        previous_speedup = current_speedup
    # -------------------------------------------------
    # VERIFICATION HASH
    # -------------------------------------------------

    verify = emit_verify_tag(
        "PHASE2",
        STUDENT_ID,
        observed_at_plog,
        gustafson_results[P_LOG]
    )

    print("\n" + verify)


if __name__ == "__main__":
    mp.freeze_support()
    main()
