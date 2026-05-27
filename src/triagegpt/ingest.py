"""Parsers for failing test logs in a couple of common CI formats."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import TestFailure

# pytest short-test-summary lines, e.g.
#   FAILED tests/test_api.py::test_login - ConnectionError: refused
_PYTEST_LINE = re.compile(r"^FAILED\s+(?P<test_id>\S+)\s*-\s*(?P<message>.+)$")

# JUnit-style "junit" text dumps, e.g.
#   [FAIL] com.acme.OrderTest.checkout: TimeoutException after 30s
_JUNIT_LINE = re.compile(r"^\[FAIL\]\s+(?P<test_id>\S+):\s*(?P<message>.+)$")


def parse_pytest_log(text: str) -> list[TestFailure]:
    """Parse a pytest short summary block into failures.

    The full block following each FAILED line (until the next FAILED line or
    the end) is captured as the failure log text.
    """
    return _parse(text, _PYTEST_LINE)


def parse_junit_log(text: str) -> list[TestFailure]:
    """Parse a JUnit-style text dump into failures."""
    return _parse(text, _JUNIT_LINE)


def _parse(text: str, pattern: re.Pattern[str]) -> list[TestFailure]:
    lines = text.splitlines()
    starts: list[int] = []
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            starts.append(i)

    failures: list[TestFailure] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        match = pattern.match(lines[start].strip())
        assert match is not None
        block = "\n".join(lines[start:end]).strip()
        failures.append(
            TestFailure(
                test_id=match.group("test_id"),
                message=match.group("message").strip(),
                log_text=block,
            )
        )
    return failures


def parse_log(text: str) -> list[TestFailure]:
    """Parse a log trying each known format and returning the first non-empty result."""
    for parser in (parse_pytest_log, parse_junit_log):
        failures = parser(text)
        if failures:
            return failures
    return []


def parse_logs(texts: Iterable[str]) -> list[TestFailure]:
    out: list[TestFailure] = []
    for text in texts:
        out.extend(parse_log(text))
    return out
