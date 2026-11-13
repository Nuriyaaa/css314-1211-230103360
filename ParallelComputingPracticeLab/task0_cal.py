
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
