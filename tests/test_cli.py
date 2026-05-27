import json

from triagegpt.cli import main


def _write_log(tmp_path):
    log = tmp_path / "fail.log"
    log.write_text(
        "FAILED tests/test_orders.py::test_checkout - "
        "ConnectionError: connection pool exhausted after 30s\n",
        encoding="utf-8",
    )
    return log


def test_cli_writes_json_report(tmp_path):
    log = _write_log(tmp_path)
    out = tmp_path / "triage.json"
    rc = main([str(log), "--format", "json", "--out", str(out), "--corpus-size", "120"])
    assert rc == 0
    payload = json.loads(out.read_text())
    assert payload["test_id"] == "tests/test_orders.py::test_checkout"
    assert payload["suggested_owner"] == "data-platform"


def test_cli_markdown_to_stdout(tmp_path, capsys):
    log = _write_log(tmp_path)
    rc = main([str(log), "--format", "markdown", "--corpus-size", "120"])
    assert rc == 0
    assert "Triage report" in capsys.readouterr().out


def test_cli_missing_file_returns_error(tmp_path):
    assert main([str(tmp_path / "nope.log")]) == 2


def test_cli_unparseable_log_returns_error(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("nothing to see here\n", encoding="utf-8")
    assert main([str(log)]) == 1
