from triagegpt.ingest import parse_junit_log, parse_log, parse_pytest_log

PYTEST_LOG = """\
============ short test summary ============
FAILED tests/test_api.py::test_login - ConnectionError: connection refused
    File "src/api/client.py", line 42, in connect
    ConnectionError: connection refused
FAILED tests/test_api.py::test_logout - AssertionError: expected 200 got 500
"""

JUNIT_LOG = """\
[FAIL] com.acme.OrderTest.checkout: TimeoutException after 30s
  at com.acme.Order.run(Order.java:88)
[FAIL] com.acme.OrderTest.refund: NullPointerException
"""


def test_parse_pytest_extracts_failures():
    failures = parse_pytest_log(PYTEST_LOG)
    assert [f.test_id for f in failures] == [
        "tests/test_api.py::test_login",
        "tests/test_api.py::test_logout",
    ]
    assert failures[0].message == "ConnectionError: connection refused"
    assert "File" in failures[0].log_text


def test_parse_junit_extracts_failures():
    failures = parse_junit_log(JUNIT_LOG)
    assert failures[0].test_id == "com.acme.OrderTest.checkout"
    assert failures[0].message == "TimeoutException after 30s"


def test_parse_log_picks_a_format():
    assert parse_log(JUNIT_LOG)[0].test_id == "com.acme.OrderTest.checkout"
    assert parse_log("nothing here") == []
