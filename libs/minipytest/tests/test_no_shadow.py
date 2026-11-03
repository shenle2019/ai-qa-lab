import pytest

import libs.minipytest


def test_real_pytest_is_still_the_installed_pytest():
    assert pytest.__version__ == "8.3.4"
    assert ".venv" in pytest.__file__.lower()


def test_minipytest_exports_its_own_version():
    assert libs.minipytest.__version__ == "0.1.0"
