## Triage report for `tests/test_auth.py::test_login`

- Error type: `AssertionError`
- Headline: AssertionError: 401 Unauthorized on valid credentials

- Suggested owner: **identity** (confidence 1.00)
- Likely root cause: auth token expiry not handled

### Similar past failures

| test | similarity | owner | root cause |
| --- | --- | --- | --- |
| `tests/test_auth.py::test_login` | 1.000 | identity | auth token expiry not handled |
| `tests/test_auth.py::test_login` | 1.000 | identity | auth token expiry not handled |
| `tests/test_auth.py::test_login` | 0.992 | identity | auth token expiry not handled |
| `tests/test_auth.py::test_login` | 0.992 | identity | auth token expiry not handled |
| `tests/test_auth.py::test_login` | 0.992 | identity | auth token expiry not handled |
