"""Owner attribution and the CI artifact emitted for auto-posting.

The owner ranking is aggregated from the retrieved neighbors by the suggester;
this module exposes it as a small attribution view and renders the deterministic
check payload a CI step posts back to the run.
"""

from __future__ import annotations

from .models import TriageResult


def ranked_owners(result: TriageResult) -> list[tuple[str, float]]:
    """Owners ranked by aggregated, normalized weight from the neighbors."""
    return [(v.owner, round(v.weight, 4)) for v in result.owner_votes]


def check_run_payload(result: TriageResult) -> dict[str, object]:
    """A check-run style payload suitable for posting into a CI pipeline.

    Mirrors the shape a CI step would attach to a failing run: a conclusion, a
    title, and a summary carrying the attributed owner and supporting neighbors.
    """
    s = result.summary
    if result.confident_match:
        conclusion = "action_required"
        title = f"Triage: {s.test_id} likely owned by {result.suggested_owner}"
    else:
        conclusion = "neutral"
        title = f"Triage: {s.test_id} no confident match"

    return {
        "name": "triagegpt",
        "conclusion": conclusion,
        "title": title,
        "test_id": s.test_id,
        "error_type": s.error_type,
        "suggested_owner": result.suggested_owner,
        "owner_confidence": result.owner_confidence,
        "suggested_root_cause": result.suggested_root_cause,
        "ranked_owners": [
            {"owner": owner, "weight": weight} for owner, weight in ranked_owners(result)
        ],
        "supporting_neighbors": [
            {
                "test_id": n.failure.test_id,
                "similarity": round(n.similarity, 4),
                "owner": n.failure.owner,
            }
            for n in result.neighbors
        ],
    }
