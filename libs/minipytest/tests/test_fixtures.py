def test_fixture_scopes_and_teardown_order(run_suite, tmp_path):
    result = run_suite(
        {
            "conftest.py": """
                from pathlib import Path
                from libs.minipytest import fixture

                LOG = Path(__file__).with_name("log.txt")

                def note(text):
                    with LOG.open("a", encoding="utf-8") as handle:
                        handle.write(text + "\\n")

                @fixture(scope="session")
                def s():
                    note("s:setup")
                    yield "s"
                    note("s:teardown")

                @fixture(scope="module")
                def m():
                    note("m:setup")
                    yield "m"
                    note("m:teardown")

                @fixture
                def f():
                    note("f:setup")
                    yield "f"
                    note("f:teardown")
            """,
            "test_scope.py": """
                from pathlib import Path

                LOG = Path(__file__).with_name("log.txt")

                def note(text):
                    with LOG.open("a", encoding="utf-8") as handle:
                        handle.write(text + "\\n")

                def test_one(s, m, f):
                    note("one")

                def test_two(s, m, f):
                    note("two")
            """,
        }
    )
    assert result.summary["passed"] == 2
    log = (tmp_path / "log.txt").read_text(encoding="utf-8").splitlines()
    assert log == [
        "s:setup",
        "m:setup",
        "f:setup",
        "one",
        "f:teardown",
        "f:setup",
        "two",
        "f:teardown",
        "m:teardown",
        "s:teardown",
    ]


def test_fixture_dependency_injection(run_suite):
    result = run_suite(
        {
            "test_dep.py": """
                from libs.minipytest import assert_that, fixture

                @fixture
                def base():
                    return 2

                @fixture
                def doubled(base):
                    return base * 2

                def test_doubled(doubled):
                    assert_that(doubled).is_equal_to(4)
            """
        }
    )
    assert result.summary["passed"] == 1


def test_autouse_fixture_runs(run_suite, tmp_path):
    result = run_suite(
        {
            "conftest.py": """
                from pathlib import Path
                from libs.minipytest import fixture

                LOG = Path(__file__).with_name("log.txt")

                @fixture(autouse=True)
                def auto():
                    with LOG.open("a", encoding="utf-8") as handle:
                        handle.write("auto\\n")
            """,
            "test_auto.py": """
                from pathlib import Path

                def test_auto():
                    with Path(__file__).with_name("log.txt").open("a", encoding="utf-8") as handle:
                        handle.write("test\\n")
            """,
        }
    )
    assert result.summary["passed"] == 1
    assert (tmp_path / "log.txt").read_text(encoding="utf-8").splitlines() == ["auto", "test"]


def test_fixture_setup_error(run_suite):
    result = run_suite(
        {
            "test_setup_error.py": """
                from libs.minipytest import fixture

                @fixture
                def bad():
                    raise RuntimeError("setup boom")

                def test_bad(bad):
                    pass
            """
        }
    )
    item = result.tests[0]
    assert item.status == "error"
    assert item.phase == "setup"
    assert "setup boom" in item.failure.message
    assert result.exit_code == 1


def test_fixture_teardown_error(run_suite):
    result = run_suite(
        {
            "test_teardown_error.py": """
                from libs.minipytest import fixture

                @fixture
                def bad():
                    yield "ok"
                    raise RuntimeError("teardown boom")

                def test_bad(bad):
                    pass
            """
        }
    )
    item = result.tests[0]
    assert item.status == "error"
    assert item.phase == "teardown"
    assert "teardown boom" in item.failure.message
    assert len(item.teardown_errors) == 1


def test_nearest_conftest_wins(run_suite):
    result = run_suite(
        {
            "conftest.py": """
                from libs.minipytest import fixture

                @fixture
                def value():
                    return 1
            """,
            "sub/conftest.py": """
                from libs.minipytest import fixture

                @fixture
                def value():
                    return 2
            """,
            "sub/test_value.py": """
                from libs.minipytest import assert_that

                def test_value(value):
                    assert_that(value).is_equal_to(2)
            """,
        }
    )
    assert result.summary["passed"] == 1
