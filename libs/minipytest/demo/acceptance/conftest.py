from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from libs.minipytest import fixture

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "apps" / "sut" / "backend"

STATE = {"autouse": False}
FUNCTION_COUNTER = {"n": 0}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(f"{url}/health", timeout=1).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"SUT did not become ready: {url}")


@fixture(scope="session")
def session_value():
    return {"count": 0}


@fixture(scope="module")
def module_value():
    return {"count": 0}


@fixture
def function_value():
    FUNCTION_COUNTER["n"] += 1
    return FUNCTION_COUNTER["n"]


@fixture(autouse=True)
def autouse_flag():
    STATE["autouse"] = True


@fixture
def state():
    return STATE


@fixture(scope="session")
def sut():
    tmp = Path(tempfile.mkdtemp(prefix="minipytest-sut-"))
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{(tmp / 'demo.db').as_posix()}"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            str(BACKEND),
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready(url)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


@fixture
def api(sut):
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    try:
        yield sut, session
    finally:
        session.close()
