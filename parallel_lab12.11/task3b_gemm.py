
import os
import time
import statistics
import multiprocessing as mp

STUDENT_ID = 230103360
N = 384
TILE_SIZES = [4, 8, 12, 16, 24, 32, 48, 64, 96, 128]


def create_matrices():
    A = [[(i + j) % 10 / 10.0 for j in range(N)] for i in range(N)]
    B = [[(i * j + 1) % 10 / 10.0 for j in range(N)] for i in range(N)]
    return A, B


def gemm_ijk(A, B):
    C = [[0.0] * N for _ in range(N)]

    for i in range(N):
        for j in range(N):
            total = 0.0
            for k in range(N):
                total += A[i][k] * B[k][j]
            C[i][j] = total

    return C


def gemm_ikj(A, B):
    C = [[0.0] * N for _ in range(N)]

    for i in range(N):
        for k in range(N):
            a = A[i][k]
            for j in range(N):
                C[i][j] += a * B[k][j]

    return C


def gemm_tiled(A, B, tile):
    C = [[0.0] * N for _ in range(N)]

    for ii in range(0, N, tile):
        for jj in range(0, N, tile):
            for kk in range(0, N, tile):

                i_end = min(ii + tile, N)
                j_end = min(jj + tile, N)
                k_end = min(kk + tile, N)

                for i in range(ii, i_end):
                    for k in range(kk, k_end):
                        a = A[i][k]
                        for j in range(jj, j_end):
                            C[i][j] += a * B[k][j]

    return C


def checksum(C):
    return sum(sum(row) for row in C)


def benchmark(name, function):
    start = time.perf_counter()
    C = function()
    elapsed = (time.perf_counter() - start) * 1000

    result = checksum(C)
    print(f"{name:<20} {elapsed:>12.3f} ms   checksum={result:.6f}")

    return elapsed, result


def main():
    print("=" * 65)
    print("PHASE 3B: MATRIX MULTIPLICATION (GEMM)")
    print("=" * 65)
    print(f"Student ID: {STUDENT_ID}")
    print(f"Matrix size: {N} x {N}")
    print(f"Logical CPUs: {mp.cpu_count()}")

    A, B = create_matrices()

    print("\n1. NAIVE i-j-k")
    print("-" * 65)
    t_ijk, hash_ijk = benchmark(
        "Naive i-j-k",
        lambda: gemm_ijk(A, B)
    )

    print("\n2. REORDERED i-k-j")
    print("-" * 65)
    t_ikj, hash_ikj = benchmark(
        "Reordered i-k-j",
        lambda: gemm_ikj(A, B)
    )

    print("\n3. TILED MATRIX MULTIPLICATION")
    print("-" * 65)

    tiled_results = []

    for tile in TILE_SIZES:
        elapsed, result = benchmark(
            f"Tile size {tile}",
            lambda tile=tile: gemm_tiled(A, B, tile)
        )
        tiled_results.append((tile, elapsed, result))

    print("\n4. PERFORMANCE SUMMARY")
    print("-" * 65)

    print(f"Naive i-j-k:       {t_ijk:.3f} ms")
    print(f"Reordered i-k-j:   {t_ikj:.3f} ms")
    print(f"Reordering speedup: {t_ijk / t_ikj:.3f}x")

    best_tile = min(tiled_results, key=lambda x: x[1])

    print(f"\nBest tile size:    {best_tile[0]}")
    print(f"Best tiled time:   {best_tile[1]:.3f} ms")
    print(f"Tiled speedup:     {t_ijk / best_tile[1]:.3f}x")

    print("\n5. CORRECTNESS CHECK")
    print("-" * 65)

    all_results = [hash_ijk, hash_ikj] + [
        item[2] for item in tiled_results
    ]

    reference = all_results[0]
    passed = all(
        abs(value - reference) < 1e-6
        for value in all_results
    )

    print("All implementations match:", passed)

    print("\nPHASE 3B COMPLETED" if passed else "\nCHECK FAILED")


if __name__ == "__main__":
    main()
