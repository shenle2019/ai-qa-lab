"""Screenshot the seeded dataset so the numbers are visible, not just in JSON."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "dataset" / "shots"
UI = "http://127.0.0.1:8000/ui/"

PAGES = [
    ("overview", "#/overview", "dataset-overview.png"),
    ("projects", "#/projects", "dataset-projects.png"),
    ("requirements", "#/requirements", "dataset-requirements.png"),
    ("functional", "#/functional", "dataset-functional.png"),
    ("knowledge", "#/kb", "dataset-knowledge.png"),
    ("api", "#/api-automation", "dataset-api-automation.png"),
    ("ui", "#/ui-automation", "dataset-ui-automation.png"),
    ("environments", "#/environments", "dataset-environments.png"),
    ("modules", "#/modules", "dataset-modules.png"),
    ("members", "#/members", "dataset-members.png"),
    ("users", "#/users", "dataset-users.png"),
    ("system-ai", "#/system-ai", "dataset-system-ai.png"),
]


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        for key, path, shot in PAGES:
            page.goto(UI + path, wait_until="networkidle")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(SHOTS / shot), full_page=True)
            print("ok", key, flush=True)
        print("pageerrors", len(errors))
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
