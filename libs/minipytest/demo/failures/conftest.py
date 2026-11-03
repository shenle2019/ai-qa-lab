from libs.minipytest import fixture


@fixture
def setup_boom():
    raise RuntimeError("fixture setup boom")


@fixture
def teardown_boom():
    yield "ok"
    raise RuntimeError("fixture teardown boom")
