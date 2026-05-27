"""Owner attribution and CI check payload."""

from triagegpt.attribution import check_run_payload, ranked_owners
from triagegpt.index import FailureIndex
from triagegpt.pipeline import TriagePipeline
from triagegpt.synthetic import generate_corpus, generate_query, novel_failure


def _pipeline(seed=5):
    index = FailureIndex()
    index.add_all(generate_corpus(300, seed=seed))
    return TriagePipeline(index, k=5)


def test_seeded_failure_maps_to_expected_owner():
    # archetype 2 is the payment gateway timeout family owned by payments
    result = _pipeline().triage(generate_query(2))
    assert result.suggested_owner == "payments"
    owners = ranked_owners(result)
    assert owners[0][0] == "payments"
    assert 0.0 < owners[0][1] <= 1.0


def test_check_payload_has_required_fields():
    result = _pipeline().triage(generate_query(2))
    payload = check_run_payload(result)
    for field in (
        "name",
        "conclusion",
        "title",
        "suggested_owner",
        "owner_confidence",
        "ranked_owners",
        "supporting_neighbors",
    ):
        assert field in payload
    assert payload["conclusion"] == "action_required"
    assert payload["suggested_owner"] == "payments"
    assert payload["supporting_neighbors"]


def test_check_payload_neutral_for_novel_failure():
    payload = check_run_payload(_pipeline().triage(novel_failure()))
    assert payload["conclusion"] == "neutral"
    assert payload["suggested_owner"] is None
