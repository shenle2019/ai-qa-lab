import pytest

from libs.minipytest.errors import UsageError
from libs.minipytest.markers import parse_marker_expr


def test_skip_xfail_xpass_and_retry(run_suite):
    result = run_suite(
        {
            "test_markers.py": """
                from libs.minipytest import assert_that, mark

                count = {"n": 0}

                @mark.skip("skip me")
                def test_skip():
                    raise AssertionError("should not run")

                @mark.xfail("expected failure")
                def test_xfail():
                    assert_that(1).is_equal_to(2)

                @mark.xfail("expected pass")
                def test_xpass():
                    pass

                @mark.xfail("strict", strict=True)
                def test_strict_xpass():
                    pass

                @mark.retry(2)
                def test_flaky():
                    count["n"] += 1
                    assert count["n"] >= 2

                @mark.smoke
                def test_smoke():
                    pass
            """
        }
    )
    statuses = {item.case.name: item.status for item in result.tests}
    assert statuses["test_skip"] == "skipped"
    assert statuses["test_xfail"] == "xfailed"
    assert statuses["test_xpass"] == "xpassed"
    assert statuses["test_strict_xpass"] == "failed"
    assert statuses["test_flaky"] == "passed"
    assert statuses["test_smoke"] == "passed"
    assert result.summary["retried"] == 1
    assert result.summary["flaky"] == 1
    assert result.exit_code == 1


def test_marker_filter_deselects(run_suite):
    result = run_suite(
        {
            "test_filter.py": """
                from libs.minipytest import mark

                @mark.smoke
                def test_smoke():
                    pass

                def test_other():
                    pass
            """
        },
        marker_expr="smoke",
    )
    assert result.summary["total"] == 1
    assert result.summary["deselected"] == 1
    assert result.tests[0].case.name == "test_smoke"


def test_marker_expression_parser():
    predicate = parse_marker_expr("smoke and not slow")
    assert predicate({"smoke"}) is True
    assert predicate({"smoke", "slow"}) is False
    assert parse_marker_expr("slow or quarantine")({"quarantine"}) is True
    assert parse_marker_expr(None)({"anything"}) is True


def test_invalid_marker_expression():
    with pytest.raises(UsageError):
        parse_marker_expr("smoke and (")


def test_skip_mark_does_not_setup_fixtures(run_suite, tmp_path):
    result = run_suite(
        {
            "conftest.py": """
                from pathlib import Path
                from libs.minipytest import fixture

                LOG = Path(__file__).with_name("log.txt")

                @fixture(autouse=True)
                def auto():
                    LOG.write_text("ran", encoding="utf-8")
                    yield
            """,
            "test_skip_fixture.py": """
                from libs.minipytest import mark

                @mark.skip("no setup")
                def test_skip():
                    pass
            """,
        }
    )
    assert result.summary["skipped"] == 1
    assert not (tmp_path / "log.txt").exists()
