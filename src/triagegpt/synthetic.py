"""Deterministic synthetic generator for CI runs with seeded failures.

Each synthetic failure carries a known root cause and owner so it can be used
both as a past-failure corpus (with labels) and as a query (labels hidden).
"""

from __future__ import annotations

import random

from .models import TestFailure

# Each archetype is a recurring failure family: a stable root cause and owner,
# plus templates whose wording varies between runs.
_ARCHETYPES: tuple[dict[str, object], ...] = (
    {
        "root_cause": "database connection pool exhausted",
        "owner": "data-platform",
        "error_type": "ConnectionError",
        "tests": ["tests/test_orders.py::test_checkout", "tests/test_orders.py::test_refund"],
        "messages": [
            "ConnectionError: connection pool exhausted after 30s",
            "ConnectionError: could not acquire connection from pool",
            "ConnectionError: pool timeout waiting for free slot",
        ],
    },
    {
        "root_cause": "auth token expiry not handled",
        "owner": "identity",
        "error_type": "AssertionError",
        "tests": ["tests/test_auth.py::test_login", "tests/test_auth.py::test_session_refresh"],
        "messages": [
            "AssertionError: expected 200 got 401 after token refresh",
            "AssertionError: session rejected with expired token",
            "AssertionError: 401 Unauthorized on valid credentials",
        ],
    },
    {
        "root_cause": "flaky timeout in payment gateway stub",
        "owner": "payments",
        "error_type": "TimeoutException",
        "tests": ["tests/test_pay.py::test_capture", "tests/test_pay.py::test_authorize"],
        "messages": [
            "TimeoutException: gateway stub did not respond in 10s",
            "TimeoutException: read timeout from payment sandbox",
            "TimeoutException: capture call exceeded deadline",
        ],
    },
    {
        "root_cause": "off by one in pagination cursor",
        "owner": "search",
        "error_type": "IndexError",
        "tests": ["tests/test_search.py::test_page", "tests/test_search.py::test_scroll"],
        "messages": [
            "IndexError: list index out of range at cursor boundary",
            "IndexError: page offset beyond result set",
            "IndexError: cursor advanced past final page",
        ],
    },
    {
        "root_cause": "schema migration drift in staging",
        "owner": "data-platform",
        "error_type": "OperationalError",
        "tests": ["tests/test_reports.py::test_daily", "tests/test_reports.py::test_rollup"],
        "messages": [
            "OperationalError: column revenue_cents does not exist",
            "OperationalError: relation report_daily missing",
            "OperationalError: unknown column in aggregate query",
        ],
    },
)


def _make_failure(rng: random.Random, archetype: dict[str, object], labeled: bool) -> TestFailure:
    tests = archetype["tests"]
    messages = archetype["messages"]
    assert isinstance(tests, list)
    assert isinstance(messages, list)
    test_id = rng.choice(tests)
    message = rng.choice(messages)
    stack = "\n".join(
        f'  File "src/{archetype["owner"]}/handler.py", line {rng.randint(10, 400)}, in run'
        for _ in range(rng.randint(2, 4))
    )
    log_text = f"FAILED {test_id} - {message}\n{stack}\n{message}"
    return TestFailure(
        test_id=test_id,
        message=message,
        log_text=log_text,
        root_cause=str(archetype["root_cause"]) if labeled else None,
        owner=str(archetype["owner"]) if labeled else None,
    )


def generate_corpus(count: int, seed: int = 0, labeled: bool = True) -> list[TestFailure]:
    """Generate a corpus of past failures drawn from the recurring archetypes."""
    rng = random.Random(seed)
    return [_make_failure(rng, rng.choice(_ARCHETYPES), labeled) for _ in range(count)]


def generate_query(archetype_index: int, seed: int = 999) -> TestFailure:
    """Generate one unlabeled query failure from a chosen archetype."""
    rng = random.Random(seed)
    return _make_failure(rng, _ARCHETYPES[archetype_index], labeled=False)


def novel_failure() -> TestFailure:
    """A failure unlike any archetype, used to test the no-confident-match path."""
    return TestFailure(
        test_id="tests/test_telemetry.py::test_export",
        message="ValueError: unsupported metric encoding 'protobuf-v9'",
        log_text=(
            "FAILED tests/test_telemetry.py::test_export - "
            "ValueError: unsupported metric encoding 'protobuf-v9'\n"
            "  File \"src/telemetry/export.py\", line 88, in encode\n"
            "ValueError: unsupported metric encoding 'protobuf-v9'"
        ),
    )


def archetype_labels() -> list[tuple[str, str]]:
    """Return (root_cause, owner) for each archetype in order."""
    return [(str(a["root_cause"]), str(a["owner"])) for a in _ARCHETYPES]


def archetype_count() -> int:
    return len(_ARCHETYPES)


def labeled_queries(per_archetype: int = 3, seed: int = 7000) -> list[tuple[TestFailure, str, str]]:
    """Build labeled query cases: (query, true_root_cause, true_owner).

    Each query is drawn from a known archetype with a distinct seed, so its true
    archetype identity is known regardless of which template wording it gets.
    """
    cases: list[tuple[TestFailure, str, str]] = []
    for idx, archetype in enumerate(_ARCHETYPES):
        for j in range(per_archetype):
            rng = random.Random(seed + idx * 100 + j)
            query = _make_failure(rng, archetype, labeled=False)
            cases.append((query, str(archetype["root_cause"]), str(archetype["owner"])))
    return cases
