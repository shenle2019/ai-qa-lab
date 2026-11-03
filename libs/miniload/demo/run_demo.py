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

from libs.miniload import Scenario, run_load, write_html_report, write_json_report

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "apps" / "sut" / "backend"
OUT = ROOT / "docs" / "portfolio"


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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="miniload-sut-"))
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
        result = run_load(
            Scenario("SUT health", "GET", url + "/health", timeout=5),
            vus=20,
            duration=5,
            ramp_up=1,
            p95_ms=500,
            error_rate=0.01,
            min_rps=10,
        )
        write_json_report(result, OUT / "module-06-load-report.json")
        write_html_report(result, OUT / "module-06-load-report.html")
        print(
            f"{result.total} requests · {result.rps:.1f} rps · "
            f"p95 {result.percentiles['p95']}ms · error {result.error_rate:.2%} · "
            f"{'PASS' if result.passed else 'FAIL'}"
        )
        for violation in result.violations:
            print(f"- {violation}")
        return 0 if result.passed else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
