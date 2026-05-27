"""End to end triage pipeline wiring the provider seam, index and suggester."""

from __future__ import annotations

from .index import FailureIndex
from .models import TestFailure, TriageResult
from .providers import DeterministicSummaryProvider, SummaryProvider
from .suggest import suggest


class TriagePipeline:
    """Summarize a failure, retrieve similar past failures and suggest owner."""

    def __init__(
        self,
        index: FailureIndex,
        summarizer: SummaryProvider | None = None,
        k: int = 5,
    ) -> None:
        self._index = index
        self._summarizer = summarizer or DeterministicSummaryProvider()
        self._k = k

    def triage(self, failure: TestFailure) -> TriageResult:
        summary = self._summarizer.summarize(failure)
        neighbors = self._index.query(failure, k=self._k)
        return suggest(summary, failure, neighbors)
