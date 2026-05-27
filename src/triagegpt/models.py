"""Core data structures shared across the triage pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TestFailure:
    """A single failing test extracted from a CI log."""

    test_id: str
    message: str
    log_text: str
    root_cause: str | None = None
    owner: str | None = None

    def signature(self) -> str:
        """Text used for summarization and embedding."""
        return f"{self.test_id}\n{self.message}\n{self.log_text}".strip()


@dataclass(frozen=True)
class FailureSummary:
    """Structured summary produced by the summarization provider."""

    test_id: str
    headline: str
    error_type: str
    key_lines: tuple[str, ...]

    def is_valid(self) -> bool:
        return bool(self.test_id) and bool(self.headline) and bool(self.error_type)


@dataclass(frozen=True)
class Neighbor:
    """A retrieved past failure with its similarity to the query."""

    failure: TestFailure
    similarity: float


@dataclass(frozen=True)
class OwnerVote:
    owner: str
    weight: float


@dataclass(frozen=True)
class TriageResult:
    """End to end triage output for one new failure."""

    summary: FailureSummary
    neighbors: tuple[Neighbor, ...]
    suggested_root_cause: str | None
    suggested_owner: str | None
    owner_confidence: float
    owner_votes: tuple[OwnerVote, ...] = field(default_factory=tuple)

    @property
    def confident_match(self) -> bool:
        return self.suggested_owner is not None
