import pytest

from libs.minipytest import AssertionFailure, assert_that, raises


def test_equal_failure_carries_values_and_diff():
    with pytest.raises(AssertionFailure) as ctx:
        assert_that({"status": "closed"}).is_equal_to({"status": "open"})
    failure = ctx.value
    assert failure.expected == {"status": "open"}
    assert failure.actual == {"status": "closed"}
    assert "'status': 'open'" in failure.diff
    assert "'status': 'closed'" in failure.diff
    assert "-" in failure.diff and "+" in failure.diff


def test_chaining_and_comparisons():
    assert_that(4).is_greater_than(3).is_less_than(5).is_in([1, 4, 9])
    assert_that("hello").contains("ell").matches("^h.*o$")
    assert_that([1, 2, 3]).has_length(3)
    assert_that(None).is_none()
    assert_that(3.14159).is_close_to(3.14, abs_tol=0.01)


def test_raises_success_and_message_match():
    with raises(ValueError, match="boom") as ctx:
        raise ValueError("boom happened")
    assert "boom" in str(ctx.value)


def test_raises_without_exception_fails():
    with pytest.raises(AssertionFailure):
        with raises(ValueError):
            pass


def test_raises_wrong_type_fails():
    with pytest.raises(AssertionFailure):
        with raises(ValueError):
            raise TypeError("wrong")


def test_custom_message_is_in_failure():
    with pytest.raises(AssertionFailure) as ctx:
        assert_that(1, "ticket count").is_equal_to(2)
    assert "ticket count" in str(ctx.value)
