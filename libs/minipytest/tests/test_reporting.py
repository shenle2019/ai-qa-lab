import json

from libs.minipytest import write_html_report, write_json_report


def test_json_report_summary_and_attempts(run_suite, tmp_path):
    result = run_suite(
        {
            "test_report.py": """
                from libs.minipytest import assert_that, mark, parametrize

                def test_pass():
                    pass

                def test_fail():
                    assert_that(1).is_equal_to(2)

                @mark.skip("skip")
                def test_skip():
                    pass

                @mark.xfail("xfail")
                def test_xfail():
                    assert_that(1).is_equal_to(2)

                @parametrize("value", ["<script>alert(1)</script>"])
                def test_escape(value):
                    assert_that(value).contains("alert")
            """
        }
    )
    target = tmp_path / "report.json"
    write_json_report(result, target)
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["summary"]["total"] == 5
    assert data["summary"]["passed"] == 2
    assert data["summary"]["failed"] == 1
    assert data["summary"]["skipped"] == 1
    assert data["summary"]["xfailed"] == 1
    statuses = {item["name"]: item["status"] for item in data["tests"]}
    assert statuses["test_fail"] == "failed"


def test_html_report_is_offline_and_escaped(run_suite, tmp_path):
    result = run_suite(
        {
            "test_escape.py": """
                from libs.minipytest import assert_that, parametrize

                @parametrize("value", ["<script>alert(1)</script>"])
                def test_escape(value):
                    assert_that(value).contains("alert")
            """
        }
    )
    target = tmp_path / "report.html"
    write_html_report(result, target)
    text = target.read_text(encoding="utf-8")
    assert "<html" in text
    assert "&lt;script&gt;" in text
    assert "<script>alert(1)</script>" not in text
    assert "http://" not in text
    assert "https://" not in text


def test_html_report_contains_failure_details(run_suite, tmp_path):
    result = run_suite(
        {
            "test_fail.py": """
                from libs.minipytest import assert_that

                def test_fail():
                    assert_that({"a": 1}).is_equal_to({"a": 2})
            """
        }
    )
    target = tmp_path / "fail.html"
    write_html_report(result, target)
    text = target.read_text(encoding="utf-8")
    assert "values are not equal" in text
    assert "expected" in text
    assert "actual" in text
    assert "diff" in text
