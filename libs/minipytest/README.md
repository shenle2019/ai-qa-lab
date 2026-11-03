# minipytest

Module 02 of AI QA Lab: a small, clean-room pytest-like runner. It does not import, wrap, or copy pytest. The package name is `minipytest`, imported as `libs.minipytest`, so the real `pytest` installation is untouched.

## What it supports

- Test discovery: `test_*.py`, module-level `test_*`, `Test*` classes
- Fixtures: function / module / session scopes, dependency injection, yield teardown, autouse
- Parametrization: single and stacked `@parametrize`, custom ids, `param(..., marks=...)`
- Markers: `skip`, `skipif`, `xfail`, `retry`, arbitrary tags, `-m` expressions
- Assertions: fluent `assert_that(...)` with expected/actual and unified diff; `raises()` context
- Retry: global `--retry` and per-test `@mark.retry(n)`
- Reports: JSON schema and a self-contained offline HTML report
- Exit codes: 0 green, 1 failures/errors, 2 usage/collection, 3 no selected cases

## Usage

From the repository root:

```bash
# Run the acceptance demo
.venv/Scripts/python.exe -m libs.minipytest libs/minipytest/demo/acceptance -v \
  --json docs/portfolio/module-02-minipytest-report.json \
  --html docs/portfolio/module-02-minipytest-report.html

# Filter markers
.venv/Scripts/python.exe -m libs.minipytest libs/minipytest/demo/acceptance -m "smoke and not slow" -v

# Run the deliberate failure suite
.venv/Scripts/python.exe -m libs.minipytest libs/minipytest/demo/failures -v
```

Framework meta-tests use the real pytest:

```bash
.venv/Scripts/python.exe -m pytest libs/minipytest/tests -q
```

## Write a test

```python
from libs.minipytest import assert_that, fixture, mark, parametrize, raises

@fixture(scope="session")
def api():
    client = make_client()
    yield client
    client.close()

@parametrize("role", ["admin", "viewer"])
def test_permission(api, role):
    response = api.get("/api/tickets")
    assert_that(response.status_code).is_equal_to(200)
    assert_that(role).is_in(["admin", "viewer"])

@mark.retry(2)
def test_flaky():
    ...
```

## Layout

| File | Purpose |
|------|---------|
| `model.py` | Cases, results, failures, run summary |
| `assertions.py` | Fluent assertions and `raises` |
| `markers.py` | Mark decorators, parametrization specs, `-m` parser |
| `collect.py` | Discovery, conftest loading, parametrization expansion |
| `fixtures.py` | fixture decorator and scoped dependency injection |
| `runner.py` | Execution, retry, skip/xfail, exit code |
| `reporting.py` | JSON and offline HTML reports |
| `cli.py` | `python -m libs.minipytest` |

## Explicit non-goals

No plugin/hook system, no class/package/parametrized fixtures, no indirect fixtures, no async, no `pytest.ini`, no parallel execution, no coverage or Allure integration. Those are intentionally out of scope for this module.
