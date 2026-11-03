import json

from libs.minieval import EvalCase, MockJudge, evaluate, load_jsonl, run_compare, write_html_report


def _case(baseline: str = "不知道") -> EvalCase:
    return EvalCase(
        id="health",
        input="健康检查接口是什么？",
        actual_output="GET /health 返回 status 和 service",
        expected_output="GET /health 返回 status 和 service",
        context=["健康检查接口是 GET /health，返回 status 和 service。"],
        baseline_output=baseline,
    )


def test_load_jsonl(tmp_path):
    target = tmp_path / "data.jsonl"
    target.write_text(json.dumps({"id": "1", "input": "q", "actual_output": "a", "expected_output": "a"}) + "\n", encoding="utf-8")
    cases = load_jsonl(target)
    assert len(cases) == 1
    assert cases[0].id == "1"


def test_mock_judge_prefers_good_answer():
    good = MockJudge().score(_case())
    bad = MockJudge().score(EvalCase(
        id="bad",
        input="健康检查接口是什么？",
        actual_output="不知道",
        expected_output="GET /health 返回 status 和 service",
        context=["健康检查接口是 GET /health，返回 status 和 service。"],
    ))
    assert good["overall"] > bad["overall"]


def test_evaluate_threshold():
    cases = [_case()]
    passed = evaluate(cases, MockJudge(), threshold=0.5)
    failed = evaluate(cases, MockJudge(), threshold=0.99)
    assert passed.passed
    assert not failed.passed
    assert failed.failures == ["health"]


def test_compare_improves():
    _, candidate, comparison = run_compare([_case()], MockJudge(), threshold=0.5)
    assert candidate.passed
    assert comparison["improved"] is True
    assert comparison["delta"]["overall"] > 0


def test_html_report_is_offline(tmp_path):
    result = evaluate([_case()], MockJudge(), threshold=0.5)
    target = tmp_path / "report.html"
    write_html_report(result, target)
    text = target.read_text(encoding="utf-8")
    assert "minieval report" in text
    assert "http://" not in text
    assert "https://" not in text
