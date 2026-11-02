"""Create or update a Hugging Face Docker Space for this repo.

Usage:
    1. Put a write token in .hf_token (next to the repo root), or set HF_TOKEN.
    2. Optionally set HF_SPACE_ID (default: ai-qa-lab).
    3. Run: .venv/Scripts/python.exe scripts/deploy_hf.py

The Space only contains README.md + Dockerfile; the Dockerfile clones the
public GitHub repo at build time, so the GitHub repo remains the single source
of truth.
"""

import os
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / ".hf_token"
SPACE_FOLDER = ROOT / "deploy" / "huggingface"
SPACE_ID = os.getenv("HF_SPACE_ID", "ai-qa-lab")


def read_token() -> str:
    token = os.getenv("HF_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit("Missing token: put a write token in .hf_token or set HF_TOKEN")


def main() -> None:
    api = HfApi(token=read_token())
    username = api.whoami()["name"]
    repo_id = f"{username}/{SPACE_ID}"

    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
        private=False,
    )
    api.upload_folder(
        folder_path=str(SPACE_FOLDER),
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy AI QA Lab from GitHub",
    )
    print(f"Space: https://huggingface.co/spaces/{repo_id}")
    print(f"App:   https://{username}-{SPACE_ID}.hf.space")


if __name__ == "__main__":
    main()
