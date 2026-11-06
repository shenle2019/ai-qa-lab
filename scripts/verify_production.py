"""Verify the deployed platform (Railway) is running the current build."""

from __future__ import annotations

import json
import sys
import urllib.request

BASE = "https://ai-qa-lab-production.up.railway.app"
EXPECTED_SKILLS = 19


def get(path: str, timeout: int = 30):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main() -> int:
    failures: list[str] = []

    status, health = get("/health")
    print("health", status, health)
    if status != 200:
        failures.append("/health not 200")
    for key in ("auth", "docs", "ui_automation"):
        if key not in health:
            failures.append(f"/health missing '{key}' (old image)")

    try:
        status, skills = get("/api/platform/skills")
        print("skills", status, len(skills))
        if status != 200:
            failures.append("/api/platform/skills not 200")
        elif len(skills) != EXPECTED_SKILLS:
            failures.append(f"skills count {len(skills)} != {EXPECTED_SKILLS}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"/api/platform/skills failed: {exc}")

    for path in ("/api/platform/environments?project_id=1", "/api/platform/summary", "/api/platform/ui-cases?project_id=1"):
        try:
            status, _ = get(path)
            print(path, status)
            if status != 200:
                failures.append(f"{path} -> {status}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path} failed: {exc}")

    request = urllib.request.Request(f"{BASE}/ui/", headers={"User-Agent": "deploy-check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "ignore")
    print("/ui/ bytes", len(html))
    if 'id="app"' not in html:
        failures.append("/ui/ does not look like the built SPA")

    if failures:
        print("\nFAILED")
        for item in failures:
            print(" -", item)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
