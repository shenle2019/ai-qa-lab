from pathlib import Path

from libs.minipytest.cli import main


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_cli_passing_suite_exit_zero(tmp_path):
    _write(tmp_path / "test_ok.py", "def test_ok():\n    pass\n")
    assert main([str(tmp_path), "--rootdir", str(tmp_path)]) == 0


def test_cli_failing_suite_exit_one(tmp_path):
    _write(tmp_path / "test_bad.py", "def test_bad():\n    assert False\n")
    assert main([str(tmp_path), "--rootdir", str(tmp_path)]) == 1


def test_cli_no_selected_cases_exit_three(tmp_path):
    _write(tmp_path / "test_ok.py", "def test_ok():\n    pass\n")
    assert main([str(tmp_path), "--rootdir", str(tmp_path), "-m", "does_not_exist"]) == 3


def test_cli_invalid_marker_exit_two(tmp_path):
    _write(tmp_path / "test_ok.py", "def test_ok():\n    pass\n")
    assert main([str(tmp_path), "--rootdir", str(tmp_path), "-m", "smoke and ("]) == 2


def test_cli_writes_reports(tmp_path):
    _write(tmp_path / "test_ok.py", "def test_ok():\n    pass\n")
    json_path = tmp_path / "out.json"
    html_path = tmp_path / "out.html"
    code = main(
        [
            str(tmp_path),
            "--rootdir",
            str(tmp_path),
            "--json",
            str(json_path),
            "--html",
            str(html_path),
        ]
    )
    assert code == 0
    assert json_path.exists()
    assert html_path.exists()
