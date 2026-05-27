import json

from triagegpt.index import FailureIndex
from triagegpt.pipeline import TriagePipeline
from triagegpt.report import to_ci_markdown, to_json
from triagegpt.synthetic import generate_corpus, generate_query


def _result():
    index = FailureIndex()
    index.add_all(generate_corpus(120, seed=2))
    return TriagePipeline(index, k=5).triage(generate_query(2))


def test_json_output_round_trips():
    result = _result()
    payload = json.loads(to_json(result))
    assert payload["test_id"] == result.summary.test_id
    assert "neighbors" in payload
    assert payload["owner_confidence"] >= 0.0


def test_markdown_contains_core_fields():
    md = to_ci_markdown(_result())
    assert "## Triage report" in md
    assert "Similar past failures" in md
    assert "Suggested owner" in md
