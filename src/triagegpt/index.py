"""Embeddings index over past failures with nearest neighbor retrieval."""

from __future__ import annotations

from .models import Neighbor, TestFailure
from .providers import EmbeddingProvider, HashingEmbeddingProvider


def _cosine(a: list[float], b: list[float]) -> float:
    # Vectors are pre-normalized by the embedding provider, so the dot product
    # is the cosine similarity. Clamp to guard against float drift.
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    if dot > 1.0:
        return 1.0
    if dot < -1.0:
        return -1.0
    return dot


class FailureIndex:
    """In memory embeddings index over a corpus of past failures."""

    def __init__(self, embedder: EmbeddingProvider | None = None) -> None:
        self._embedder = embedder or HashingEmbeddingProvider()
        self._failures: list[TestFailure] = []
        self._vectors: list[list[float]] = []

    def __len__(self) -> int:
        return len(self._failures)

    def add(self, failure: TestFailure) -> None:
        self._failures.append(failure)
        self._vectors.append(self._embedder.embed(failure.signature()))

    def add_all(self, failures: list[TestFailure]) -> None:
        for failure in failures:
            self.add(failure)

    def query(self, failure: TestFailure, k: int = 5) -> list[Neighbor]:
        """Return up to k most similar past failures ranked by similarity."""
        if k <= 0 or not self._failures:
            return []
        query_vec = self._embedder.embed(failure.signature())
        scored = [
            Neighbor(failure=past, similarity=_cosine(query_vec, vec))
            for past, vec in zip(self._failures, self._vectors, strict=True)
        ]
        scored.sort(key=lambda n: n.similarity, reverse=True)
        return scored[:k]
