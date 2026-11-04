"""Performance scenarios: concurrency, duration, ramp-up and thresholds."""

import pytest

from libs.miniload import Scenario, run_load


def _load(perf_sut, path="/health", *, vus=2, duration=1, **thresholds):
    return run_load(
        Scenario("perf", "GET", perf_sut + path),
        vus=vus,
        duration=duration,
        **thresholds,
    )


@pytest.mark.parametrize("vus", [1, 2, 3, 5, 8])
def test_health_under_concurrency(perf_sut, vus):
    result = _load(perf_sut, vus=vus, p95_ms=2000, error_rate=0.01)
    assert result.passed
    assert result.total > 0
    assert result.error_rate == 0
    assert result.percentiles["p95"] > 0


@pytest.mark.parametrize("vus", [1, 2, 3, 5])
def test_ticket_list_under_concurrency(perf_sut, vus):
    result = _load(perf_sut, "/api/tickets", vus=vus, p95_ms=3000)
    assert result.passed
    assert result.status_counts.get("200", 0) == result.total


@pytest.mark.parametrize("duration", [2, 3])
def test_sustained_load(perf_sut, duration):
    result = _load(perf_sut, duration=duration, p95_ms=2000)
    assert result.passed
    assert result.total > 0
    assert result.elapsed >= duration


@pytest.mark.parametrize("ramp_up", [0.2, 0.5])
def test_ramp_up_keeps_success(perf_sut, ramp_up):
    result = run_load(
        Scenario("ramp", "GET", perf_sut + "/health"),
        vus=4,
        duration=1,
        ramp_up=ramp_up,
        p95_ms=2000,
    )
    assert result.total > 0
    assert result.error_rate == 0


@pytest.mark.parametrize("p95_ms", [200, 500, 2000])
def test_p95_thresholds_pass(perf_sut, p95_ms):
    result = _load(perf_sut, vus=3, p95_ms=p95_ms)
    assert result.passed
    assert result.percentiles["p95"] <= p95_ms


def test_p95_threshold_can_fail(perf_sut):
    result = _load(perf_sut, vus=2, p95_ms=0.001)
    assert not result.passed
    assert any("p95" in item for item in result.violations)


def test_404_is_counted_as_error(perf_sut):
    result = _load(perf_sut, "/api/tickets/999999", vus=2, error_rate=0.0)
    assert not result.passed
    assert result.error_rate > 0
    assert result.status_counts.get("404", 0) > 0


def test_error_rate_threshold(perf_sut):
    result = _load(perf_sut, "/missing", vus=2, error_rate=0.01)
    assert not result.passed
    assert any("error_rate" in item for item in result.violations)


def test_percentiles_are_ordered(perf_sut):
    result = _load(perf_sut, vus=3)
    assert result.percentiles["min"] <= result.percentiles["p50"]
    assert result.percentiles["p50"] <= result.percentiles["p95"]
    assert result.percentiles["p95"] <= result.percentiles["p99"]
    assert result.percentiles["p99"] <= result.percentiles["max"]


def test_rps_is_positive(perf_sut):
    result = _load(perf_sut, vus=2)
    assert result.rps > 0


def test_total_exceeds_vus(perf_sut):
    result = _load(perf_sut, vus=4)
    assert result.total >= result.vus


def test_min_rps_threshold(perf_sut):
    result = _load(perf_sut, vus=1, min_rps=0.01)
    assert result.passed
    assert result.thresholds["min_rps"] == 0.01


def test_min_rps_can_fail(perf_sut):
    result = _load(perf_sut, vus=1, min_rps=1_000_000)
    assert not result.passed
    assert any("rps" in item for item in result.violations)


def test_mixed_endpoint_sequence(perf_sut):
    health = _load(perf_sut, "/health", vus=2)
    tickets = _load(perf_sut, "/api/tickets", vus=2)
    assert health.passed and tickets.passed
    assert health.total > 0 and tickets.total > 0


def test_high_concurrency_health(perf_sut):
    result = _load(perf_sut, vus=10, duration=1, p95_ms=3000)
    assert result.total > 0
    assert result.error_rate == 0


def test_status_counts_present(perf_sut):
    result = _load(perf_sut, vus=2)
    assert result.status_counts.get("200", 0) > 0


def test_average_latency_is_positive(perf_sut):
    result = _load(perf_sut, vus=2)
    assert result.percentiles["avg"] > 0


def test_thresholds_are_recorded(perf_sut):
    result = _load(perf_sut, vus=1, p95_ms=2000, error_rate=0.01)
    assert result.thresholds == {"p95_ms": 2000, "error_rate": 0.01, "min_rps": None}
