"""Structured JSON output and a CI postable Markdown artifact."""

from __future__ import annotations

import json

from .models import TriageResult


def result_to_dict(result: TriageResult) -> dict[str, object]:
    """Convert a triage result into a JSON serializable dict."""
    return {
        "test_id": result.summary.test_id,
        "summary": {
            "headline": result.summary.headline,
            "error_type": result.summary.error_type,
            "key_lines": list(result.summary.key_lines),
        },
        "confident_match": result.confident_match,
        "suggested_root_cause": result.suggested_root_cause,
        "suggested_owner": result.suggested_owner,
        "owner_confidence": result.owner_confidence,
        "owner_votes": [
            {"owner": v.owner, "weight": round(v.weight, 4)} for v in result.owner_votes
        ],
        "neighbors": [
            {
                "test_id": n.failure.test_id,
                "similarity": round(n.similarity, 4),
                "root_cause": n.failure.root_cause,
                "owner": n.failure.owner,
            }
            for n in result.neighbors
        ],
    }


def to_json(result: TriageResult, indent: int = 2) -> str:
    return json.dumps(result_to_dict(result), indent=indent, sort_keys=True)


def to_ci_markdown(result: TriageResult) -> str:
    """Render a deterministic Markdown comment for posting into a CI pipeline."""
    s = result.summary
    lines: list[str] = []
    lines.append(f"## Triage report for `{s.test_id}`")
    lines.append("")
    lines.append(f"- Error type: `{s.error_type}`")
    lines.append(f"- Headline: {s.headline}")
    lines.append("")

    if result.confident_match:
        lines.append(f"- Suggested owner: **{result.suggested_owner}** "
                     f"(confidence {result.owner_confidence:.2f})")
        lines.append(f"- Likely root cause: {result.suggested_root_cause}")
    else:
        lines.append("- Suggested owner: no confident match")
        lines.append("- Likely root cause: no confident match")
    lines.append("")

    lines.append("### Similar past failures")
    if result.neighbors:
        lines.append("")
        lines.append("| test | similarity | owner | root cause |")
        lines.append("| --- | --- | --- | --- |")
        for n in result.neighbors:
            lines.append(
                f"| `{n.failure.test_id}` | {n.similarity:.3f} | "
                f"{n.failure.owner or '-'} | {n.failure.root_cause or '-'} |"
            )
    else:
        lines.append("")
        lines.append("No comparable past failures were found.")
    lines.append("")
    return "\n".join(lines)
