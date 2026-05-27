"""Benchmark indexing and retrieval over a large corpus of past failures.

Reports indexing throughput and per query retrieval latency. The numbers are
measured at run time; nothing is hard coded. ``--check`` compares against a
stored baseline and fails if any metric regresses beyond a threshold.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from triagegpt.index import FailureIndex
from triagegpt.synthetic import generate_corpus, generate_query

BASELINE_PATH = Path(__file__).parent / "baseline.json"


def run(corpus_size: int, queries: int, k: int) -> dict[str, float]:
    corpus = generate_corpus(corpus_size, seed=11)

    index = FailureIndex()
    start = time.perf_counter()
    index.add_all(corpus)
    index_seconds = time.perf_counter() - start

    probes = [generate_query(i % 5, seed=2000 + i) for i in range(queries)]
    latencies: list[float] = []
    for probe in probes:
        t0 = time.perf_counter()
        index.query(probe, k=k)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    return {
        "corpus_size": float(corpus_size),
        "queries": float(queries),
        "index_seconds": round(index_seconds, 6),
        "index_docs_per_sec": round(corpus_size / index_seconds, 2),
        "query_ms_mean": round(statistics.fmean(latencies), 4),
        "query_ms_p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 4),
    }


# Metrics where a larger value is better (throughput); the rest are latencies
# where smaller is better.
_HIGHER_IS_BETTER = {"index_docs_per_sec"}


def check(current: dict[str, float], baseline: dict[str, float], tolerance: float) -> list[str]:
    regressions: list[str] = []
    for metric in ("index_docs_per_sec", "query_ms_mean", "query_ms_p95"):
        base = baseline[metric]
        cur = current[metric]
        if metric in _HIGHER_IS_BETTER:
            if cur < base * (1.0 - tolerance):
                regressions.append(f"{metric}: {cur} below baseline {base} by >{tolerance:.0%}")
        else:
            if cur > base * (1.0 + tolerance):
                regressions.append(f"{metric}: {cur} above baseline {base} by >{tolerance:.0%}")
    return regressions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-size", type=int, default=5000)
    parser.add_argument("--queries", type=int, default=200)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--tolerance", type=float, default=0.30)
    args = parser.parse_args(argv)

    current = run(args.corpus_size, args.queries, args.k)
    print(json.dumps(current, indent=2, sort_keys=True))

    if args.write_baseline:
        BASELINE_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"wrote baseline to {BASELINE_PATH}")

    if args.check:
        if not BASELINE_PATH.exists():
            print("no baseline to check against")
            return 1
        baseline = json.loads(BASELINE_PATH.read_text())
        regressions = check(current, baseline, args.tolerance)
        if regressions:
            print("REGRESSION:")
            for r in regressions:
                print(f"  {r}")
            return 1
        print(f"no regression beyond {args.tolerance:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
