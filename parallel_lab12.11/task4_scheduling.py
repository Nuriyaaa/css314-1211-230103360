
import multiprocessing as mp
import time
import math
import statistics
import hashlib

STUDENT_ID = 230103360
N = 12_000
WORKERS = mp.cpu_count()
CHUNK_SIZES = [1, 4, 16, 64, 256, 1024]


def workload(i):
    """Skewed workload: K(i) = 1 + floor((i / 60)^2)."""
    k = 1 + (i * i) // 3600
    result = 0

    for j in range(k):
        result += i + j

    return result


def run_static_worker(indices, start_event, ready_event, output_queue):
    ready_event.set()
    start_event.wait()

    start = time.perf_counter()
    checksum = sum(workload(i) for i in indices)
    elapsed = time.perf_counter() - start

    output_queue.put((elapsed, checksum, len(indices)))


def run_dynamic_worker(task_queue, start_event, ready_event, output_queue):
    ready_event.set()
    start_event.wait()

    start = time.perf_counter()
    checksum = 0
    count = 0

    while True:
        task = task_queue.get()

        if task is None:
            break

        start_i, end_i = task

        for i in range(start_i, end_i):
            checksum += workload(i)
            count += 1

    elapsed = time.perf_counter() - start
    output_queue.put((elapsed, checksum, count))


def collect_results(output_queue, workers):
    results = [output_queue.get() for _ in range(workers)]

    times = [r[0] for r in results]
    checksum = sum(r[1] for r in results)
    count = sum(r[2] for r in results)

    return times, checksum, count


def run_static():
    context = mp.get_context("spawn")
    start_event = context.Event()
    output_queue = context.Queue()
    ready_events = [context.Event() for _ in range(WORKERS)]

    processes = []

    for worker in range(WORKERS):
        start_i = worker * N // WORKERS
        end_i = (worker + 1) * N // WORKERS
        indices = range(start_i, end_i)

        p = context.Process(
            target=run_static_worker,
            args=(indices, start_event, ready_events[worker], output_queue)
        )
        processes.append(p)
        p.start()

    for event in ready_events:
        event.wait()

    start_event.set()

    for p in processes:
        p.join()

    results = collect_results(output_queue, WORKERS)
    output_queue.close()
    return results


def run_cyclic():
    context = mp.get_context("spawn")
    start_event = context.Event()
    output_queue = context.Queue()
    ready_events = [context.Event() for _ in range(WORKERS)]

    processes = []

    for worker in range(WORKERS):
        indices = range(worker, N, WORKERS)

        p = context.Process(
            target=run_static_worker,
            args=(indices, start_event, ready_events[worker], output_queue)
        )
        processes.append(p)
        p.start()

    for event in ready_events:
        event.wait()

    start_event.set()

    for p in processes:
        p.join()

    results = collect_results(output_queue, WORKERS)
    output_queue.close()
    return results


def run_dynamic(chunk_size):
    context = mp.get_context("spawn")
    start_event = context.Event()
    task_queue = context.Queue()
    output_queue = context.Queue()
    ready_events = [context.Event() for _ in range(WORKERS)]

    for start_i in range(0, N, chunk_size):
        task_queue.put((start_i, min(start_i + chunk_size, N)))

    for _ in range(WORKERS):
        task_queue.put(None)

    processes = []

    for worker in range(WORKERS):
        p = context.Process(
            target=run_dynamic_worker,
            args=(task_queue, start_event, ready_events[worker], output_queue)
        )
        processes.append(p)
        p.start()

    for event in ready_events:
        event.wait()

    start_event.set()

    for p in processes:
        p.join()

    results = collect_results(output_queue, WORKERS)

    task_queue.close()
    output_queue.close()

    return results


def analyze(name, results):
    times, checksum, count = results

    max_time = max(times)
    min_time = min(times)
    average_time = statistics.mean(times)

    imbalance = max_time / average_time if average_time else 0

    print(f"\n{name}")
    print("-" * 65)

    for i, worker_time in enumerate(times):
        print(f"Worker {i + 1:02d}: {worker_time * 1000:.3f} ms")

    print(f"Total processed items: {count}")
    print(f"Wall-clock max worker time: {max_time * 1000:.3f} ms")
    print(f"Average worker time: {average_time * 1000:.3f} ms")
    print(f"Imbalance factor: {imbalance:.4f}")
    print(f"Checksum: {checksum}")

    return max_time, imbalance, checksum


def main():
    print("=" * 70)
    print("PHASE 4: LOAD BALANCING AND SCHEDULING")
    print("=" * 70)
    print(f"Student ID: {STUDENT_ID}")
    print(f"Total tasks: {N}")
    print(f"Workers: {WORKERS}")
    print("Workload: K(i) = 1 + floor((i / 60)^2)")

    results_summary = []

    print("\n1. STATIC CONTIGUOUS SCHEDULING")
    static_result = analyze("STATIC", run_static())
    results_summary.append(("Static", static_result))

    print("\n2. CYCLIC SCHEDULING")
    cyclic_result = analyze("CYCLIC", run_cyclic())
    results_summary.append(("Cyclic", cyclic_result))

    print("\n3. DYNAMIC SCHEDULING")
    for chunk in CHUNK_SIZES:
        result = analyze(
            f"DYNAMIC — chunk size {chunk}",
            run_dynamic(chunk)
        )
        results_summary.append((f"Dynamic {chunk}", result))

    print("\n4. SCHEDULING COMPARISON")
    print("-" * 70)
    print(f"{'Strategy':<22} {'Time (ms)':>14} {'Imbalance':>14}")

    for name, result in results_summary:
        print(f"{name:<22} {result[0] * 1000:>14.3f} {result[1]:>14.4f}")

    best = min(results_summary, key=lambda x: x[1][0])

    print("\nBest strategy:", best[0])
    print(f"Best time: {best[1][0] * 1000:.3f} ms")
    print(f"Best imbalance: {best[1][1]:.4f}")

    checksums = [item[1][2] for item in results_summary]
    correctness = all(value == checksums[0] for value in checksums)

    print("\n5. CORRECTNESS CHECK")
    print("All checksums match:", correctness)

    print("\nPHASE 4 COMPLETED" if correctness else "\nCHECK FAILED")


if __name__ == "__main__":
    mp.freeze_support()
    main()
