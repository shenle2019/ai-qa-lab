from libs.minipytest import assert_that, mark, raises


def test_nested_dict_diff():
    assert_that({"ticket": {"status": "closed", "priority": "high"}}).is_equal_to(
        {"ticket": {"status": "open", "priority": "high"}}
    )


def test_list_diff():
    assert_that([1, 2, 3]).is_equal_to([1, 4, 3])


def test_contains_failure():
    assert_that("hello world").contains("missing")


def test_regex_failure():
    assert_that("ticket-123").matches(r"^ORDER-\d+$")


def test_raises_did_not_raise():
    with raises(ValueError):
        pass


def test_raises_wrong_type():
    with raises(ValueError):
        raise TypeError("wrong type")


@mark.xfail("strict xpass should fail", strict=True)
def test_strict_xpass():
    assert_that(1).is_equal_to(1)
