"""Golden report check for a fixed seeded corpus and query."""

from pathlib import Path

from triagegpt.index import FailureIndex
from triagegpt.pipeline import TriagePipeline
from triagegpt.report import to_ci_markdown, to_json
from triagegpt.synthetic import generate_corpus, generate_query

GOLDEN = Path(__file__).parent / "golden"


def _result():
    index = FailureIndex()
    index.add_all(generate_corpus(200, seed=42))
    return TriagePipeline(index, k=5).triage(generate_query(1, seed=999))


def test_golden_json_matches():
    expected = (GOLDEN / "report.json").read_text()
    assert to_json(_result()) + "\n" == expected


def test_golden_markdown_matches():
    expected = (GOLDEN / "report.md").read_text()
    assert to_ci_markdown(_result()) == expected
