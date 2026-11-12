import time
import multiprocessing as mp

from harness import emit_verify_tag


STUDENT_ID = 230103360
CLOCK_READS = 2_000_000


def main():

    cpu_count = mp.cpu_count()

    print("PHASE 0: Hardware and Timer Calibration")
    print("---------------------------------------")

    print(f"Student ID: {STUDENT_ID}")
    print(f"Logical CPU count: {cpu_count}")

    start = time.perf_counter_ns()

    for _ in range(CLOCK_READS):
        time.perf_counter_ns()

    end = time.perf_counter_ns()

    total_ns = end - start

    average_latency_ns = total_ns / CLOCK_READS
    total_ms = total_ns / 1e6

    print(f"Clock reads: {CLOCK_READS}")
    print(f"Total elapsed time: {total_ms:.4f} ms")
    print(f"Average timer latency: {average_latency_ns:.4f} ns")

    verify = emit_verify_tag(
        "PHASE0",
        STUDENT_ID,
        average_latency_ns,
        total_ms
    )

    print()
    print(verify)


if __name__ == "__main__":
    main()