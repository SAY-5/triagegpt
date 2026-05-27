"""Root cause and owner suggestion grounded in retrieved neighbors."""

from __future__ import annotations

from collections import defaultdict

from .models import FailureSummary, Neighbor, OwnerVote, TestFailure, TriageResult

# A neighbor below this similarity is treated as not relevant. If no neighbor
# clears the floor the failure is reported as a no confident match.
DEFAULT_SIMILARITY_FLOOR = 0.35
# Minimum aggregate owner confidence required to attribute an owner.
DEFAULT_OWNER_CONFIDENCE = 0.4


def _rank_owners(neighbors: list[Neighbor]) -> list[OwnerVote]:
    weights: dict[str, float] = defaultdict(float)
    for n in neighbors:
        if n.failure.owner and n.similarity > 0:
            weights[n.failure.owner] += n.similarity
    total = sum(weights.values())
    if total == 0:
        return []
    votes = [OwnerVote(owner=o, weight=w / total) for o, w in weights.items()]
    votes.sort(key=lambda v: v.weight, reverse=True)
    return votes


def _best_root_cause(neighbors: list[Neighbor]) -> str | None:
    # Grounded only in neighbors: pick the root cause of the most similar
    # neighbor that actually carries one.
    for n in neighbors:
        if n.failure.root_cause:
            return n.failure.root_cause
    return None


def suggest(
    summary: FailureSummary,
    query: TestFailure,
    neighbors: list[Neighbor],
    similarity_floor: float = DEFAULT_SIMILARITY_FLOOR,
    owner_confidence_floor: float = DEFAULT_OWNER_CONFIDENCE,
) -> TriageResult:
    """Build a triage result from retrieved neighbors.

    Only neighbors above ``similarity_floor`` are considered. If none qualify,
    or if the aggregated owner confidence is below the floor, the result reports
    no confident match rather than forcing an owner.
    """
    relevant = [n for n in neighbors if n.similarity >= similarity_floor]

    if not relevant:
        return TriageResult(
            summary=summary,
            neighbors=tuple(neighbors),
            suggested_root_cause=None,
            suggested_owner=None,
            owner_confidence=0.0,
            owner_votes=(),
        )

    votes = _rank_owners(relevant)
    top = votes[0] if votes else None
    confident = top is not None and top.weight >= owner_confidence_floor

    return TriageResult(
        summary=summary,
        neighbors=tuple(relevant),
        suggested_root_cause=_best_root_cause(relevant) if confident else None,
        suggested_owner=top.owner if confident and top else None,
        owner_confidence=round(top.weight, 4) if top else 0.0,
        owner_votes=tuple(votes),
    )
