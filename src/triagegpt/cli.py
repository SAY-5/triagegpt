"""Command line interface for triagegpt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .attribution import check_run_payload
from .index import FailureIndex
from .ingest import parse_log
from .pipeline import TriagePipeline
from .report import to_ci_markdown, to_json
from .synthetic import generate_corpus


def _build_index(corpus_size: int, seed: int) -> FailureIndex:
    index = FailureIndex()
    index.add_all(generate_corpus(corpus_size, seed=seed))
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="triagegpt",
        description="Triage a failing test log against a corpus of past failures.",
    )
    parser.add_argument("log", type=Path, help="path to a failing test log file")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "check"],
        default="json",
        help="output format: json report, ci markdown, or check-run payload",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write the report to this file instead of stdout",
    )
    parser.add_argument("--corpus-size", type=int, default=200, help="synthetic corpus size")
    parser.add_argument("--seed", type=int, default=0, help="corpus seed")
    parser.add_argument("-k", type=int, default=5, help="number of neighbors to retrieve")
    args = parser.parse_args(argv)

    if not args.log.exists():
        print(f"log file not found: {args.log}", file=sys.stderr)
        return 2

    failures = parse_log(args.log.read_text(encoding="utf-8"))
    if not failures:
        print("no failures parsed from log", file=sys.stderr)
        return 1

    index = _build_index(args.corpus_size, args.seed)
    pipeline = TriagePipeline(index, k=args.k)
    result = pipeline.triage(failures[0])

    if args.format == "json":
        rendered = to_json(result)
    elif args.format == "markdown":
        rendered = to_ci_markdown(result)
    else:
        rendered = json.dumps(check_run_payload(result), indent=2, sort_keys=True)
    if args.out is not None:
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
