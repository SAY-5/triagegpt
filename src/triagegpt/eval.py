"""Retrieval quality evaluation: precision@k and recall over a labeled set.

An eval case pairs a query failure with the set of archetype identities that
count as correct neighbors. Here the archetype is identified by its owner and
root cause label, so a retrieved neighbor is relevant when it shares the
query's true archetype.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .index import FailureIndex
from .models import TestFailure


@dataclass(frozen=True)
class EvalCase:
    query: TestFailure
    relevant_owner: str
    relevant_root_cause: str


@dataclass(frozen=True)
class RetrievalScore:
    precision_at_k: float
    recall_at_k: float
    mean_reciprocal_rank: float


def _is_relevant(neighbor_owner: str | None, neighbor_cause: str | None, case: EvalCase) -> bool:
    return neighbor_owner == case.relevant_owner and neighbor_cause == case.relevant_root_cause


def evaluate(index: FailureIndex, cases: Sequence[EvalCase], k: int = 5) -> RetrievalScore:
    """Compute precision@k, recall@k and MRR over the labeled cases.

    Recall here is the fraction of cases for which at least one relevant prior
    failure appears in the top k (hit rate), a standard recall@k for retrieval.
    """
    if not cases:
        return RetrievalScore(0.0, 0.0, 0.0)

    precisions: list[float] = []
    hits = 0
    reciprocal_ranks: list[float] = []

    for case in cases:
        neighbors = index.query(case.query, k=k)
        flags = [
            _is_relevant(n.failure.owner, n.failure.root_cause, case) for n in neighbors
        ]
        relevant_count = sum(flags)
        precisions.append(relevant_count / len(neighbors) if neighbors else 0.0)
        if relevant_count > 0:
            hits += 1
            first = next(i for i, f in enumerate(flags) if f)
            reciprocal_ranks.append(1.0 / (first + 1))
        else:
            reciprocal_ranks.append(0.0)

    n = len(cases)
    return RetrievalScore(
        precision_at_k=round(sum(precisions) / n, 4),
        recall_at_k=round(hits / n, 4),
        mean_reciprocal_rank=round(sum(reciprocal_ranks) / n, 4),
    )
