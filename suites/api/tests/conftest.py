import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "apps" / "sut" / "backend"
TMP_DIR = ROOT / "suites" / "api" / ".tmp"


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, **kwargs):
        return self.session.get(self._url(path), timeout=10, **kwargs)

    def post(self, path: str, **kwargs):
        return self.session.post(self._url(path), timeout=10, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.session.patch(self._url(path), timeout=10, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.session.delete(self._url(path), timeout=10, **kwargs)

    def close(self) -> None:
        self.session.close()


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


@pytest.fixture(scope="session")
def base_url():
    external = os.getenv("SUT_BASE_URL")
    if external:
        yield external.rstrip("/")
        return

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    db_path = (TMP_DIR / f"test_{os.getpid()}.db").as_posix()
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"

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


@pytest.fixture()
def api(base_url):
    client = ApiClient(base_url)
    try:
        yield client
    finally:
        client.close()
