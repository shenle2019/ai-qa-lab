"""Launch a local Chromium browser and connect to its page target."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from .cdp import CDPConnection
from .errors import MiniPlaywrightError
from .page import Page

BROWSER_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/opt/google/chrome/chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _find_browser() -> str:
    configured = os.getenv("MINI_PLAYWRIGHT_BROWSER")
    if configured and Path(configured).exists():
        return configured
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise MiniPlaywrightError(
        "No Chromium browser found. Set MINI_PLAYWRIGHT_BROWSER to Edge/Chrome."
    )


def _page_target(port: int, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/json/list", timeout=1)
            targets = response.json()
            for target in targets:
                if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                    return target
            last_error = f"no page target: {targets}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise MiniPlaywrightError(f"browser did not expose a page target: {last_error}")


class Browser:
    def __init__(self, proc: subprocess.Popen, tmpdir: Path, cdp: CDPConnection, page: Page) -> None:
        self.proc = proc
        self.tmpdir = tmpdir
        self.cdp = cdp
        self.page = page

    def new_page(self) -> Page:
        return self.page

    def close(self) -> None:
        try:
            self.cdp.close()
        finally:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            except Exception:
                pass
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def launch(
    *,
    headless: bool = True,
    width: int = 1440,
    height: int = 1000,
    browser_path: str | None = None,
) -> Browser:
    executable = browser_path or _find_browser()
    tmpdir = Path(tempfile.mkdtemp(prefix="miniplaywright-"))
    port = _free_port()
    log_path = tmpdir / "browser.log"
    log_file = log_path.open("w", encoding="utf-8")

    args = [
        executable,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={tmpdir / 'profile'}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-extensions",
        "--disable-sync",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]
    if headless:
        args.append("--headless=new")
    args.append("about:blank")

    proc = subprocess.Popen(args, stdout=log_file, stderr=subprocess.STDOUT)
    try:
        target = _page_target(port)
        cdp = CDPConnection(target["webSocketDebuggerUrl"])
        page = Page(cdp, width=width, height=height)
        return Browser(proc, tmpdir, cdp, page)
    except Exception as exc:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            log_file.flush()
            log_file.close()
        except Exception:
            pass
        tail = ""
        try:
            tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-8:])
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise MiniPlaywrightError(f"browser launch failed: {exc}\n{tail}") from exc
