from libs.miniload import Scenario, run_load


def test_fast_load_passes(server):
    result = run_load(
        Scenario("fast", "GET", server + "/fast"),
        vus=5,
        duration=1,
        p95_ms=1000,
        error_rate=0.01,
    )
    assert result.passed
    assert result.total > 0
    assert result.error_rate == 0
    assert result.percentiles["p95"] > 0


def test_slow_p95_threshold_fails(server):
    result = run_load(
        Scenario("slow", "GET", server + "/slow"),
        vus=2,
        duration=1,
        p95_ms=50,
    )
    assert not result.passed
    assert any("p95" in item for item in result.violations)


def test_error_rate_threshold_fails(server):
    result = run_load(
        Scenario("error", "GET", server + "/error"),
        vus=2,
        duration=1,
        error_rate=0.01,
    )
    assert not result.passed
    assert result.error_rate > 0.01
    assert "500" in result.status_counts


def test_percentiles_are_ordered(server):
    result = run_load(Scenario("fast", "GET", server + "/fast"), vus=3, duration=1)
    assert result.percentiles["min"] <= result.percentiles["p50"]
    assert result.percentiles["p50"] <= result.percentiles["p95"]
    assert result.percentiles["p95"] <= result.percentiles["max"]


def test_ramp_up_keeps_running(server):
    result = run_load(
        Scenario("ramp", "GET", server + "/fast"),
        vus=3,
        duration=1,
        ramp_up=0.3,
    )
    assert result.total > 0
    assert result.passed
