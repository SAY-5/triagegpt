"""Provider seam for summarization and embeddings.

The pipeline depends only on the protocols below. The default implementations
are deterministic and offline so the whole tool runs hermetically in CI. A real
network backed provider can be substituted without touching the rest of the code.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from .models import FailureSummary, TestFailure

_ERROR_TYPE = re.compile(r"\b([A-Z][A-Za-z0-9]*(?:Error|Exception|Failure))\b")
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


class SummaryProvider(Protocol):
    """Turns a failure into a structured summary."""

    def summarize(self, failure: TestFailure) -> FailureSummary: ...


class EmbeddingProvider(Protocol):
    """Maps a failure signature to a fixed length vector."""

    @property
    def dim(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...


class DeterministicSummaryProvider:
    """Offline summary provider.

    Extracts the error type and the most informative log lines without any
    network call, producing a stable summary for a given input.
    """

    def summarize(self, failure: TestFailure) -> FailureSummary:
        match = _ERROR_TYPE.search(failure.message) or _ERROR_TYPE.search(failure.log_text)
        error_type = match.group(1) if match else "UnknownError"
        headline = failure.message.strip() or f"{error_type} in {failure.test_id}"
        key_lines = self._key_lines(failure.log_text)
        return FailureSummary(
            test_id=failure.test_id,
            headline=headline[:200],
            error_type=error_type,
            key_lines=key_lines,
        )

    @staticmethod
    def _key_lines(log_text: str) -> tuple[str, ...]:
        seen: list[str] = []
        for raw in log_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if _ERROR_TYPE.search(line) or line.startswith("File ") or "File \"" in line:
                if line not in seen:
                    seen.append(line)
            if len(seen) >= 5:
                break
        return tuple(seen)


class HashingEmbeddingProvider:
    """Deterministic feature hashing embedding.

    Tokens are hashed into a fixed number of buckets with a signed count, then
    the vector is L2 normalized. This gives a stable, dependency free embedding
    whose cosine similarity tracks token overlap, standing in for a network
    embedding model while keeping CI hermetic.
    """

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]
