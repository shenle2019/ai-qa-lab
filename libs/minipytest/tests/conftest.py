import textwrap
from pathlib import Path

import pytest

from libs.minipytest import run


@pytest.fixture
def run_suite(tmp_path: Path):
    def _run(files: dict[str, str], **kwargs):
        for name, content in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
        return run([tmp_path], rootdir=tmp_path, **kwargs)

    return _run
