"""Smoke test for the benchmark harness and its regression detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))

import bench_retrieval as bench  # noqa: E402


def test_bench_run_reports_metrics():
    metrics = bench.run(corpus_size=200, queries=20, k=5)
    assert metrics["index_docs_per_sec"] > 0
    assert metrics["query_ms_mean"] >= 0


def test_check_flags_latency_regression():
    baseline = {"index_docs_per_sec": 1000.0, "query_ms_mean": 10.0, "query_ms_p95": 12.0}
    worse = {"index_docs_per_sec": 1000.0, "query_ms_mean": 20.0, "query_ms_p95": 12.0}
    assert bench.check(worse, baseline, tolerance=0.30)


def test_check_passes_within_tolerance():
    baseline = {"index_docs_per_sec": 1000.0, "query_ms_mean": 10.0, "query_ms_p95": 12.0}
    similar = {"index_docs_per_sec": 950.0, "query_ms_mean": 11.0, "query_ms_p95": 12.5}
    assert bench.check(similar, baseline, tolerance=0.30) == []
