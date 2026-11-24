"""把站点（shenle-ai-qa）的 kb 手册同步进平台（ai-qa-lab）的 skill_docs。

站点是唯一事实来源：
  site/kb/skills/<slug>.md   -> 手册正文（index.md 只占位，不进列表）
  site/kb/interview-api.md   -> 面试题
  site/kb/rules.md           -> 内容更新规则
  site/public/skills/*.zip   -> 下载包（按技能目录名打包，短名页靠后端回退到 shenle-*.zip）

用法：
  python scripts/_sync_skill_docs.py --check   # 只比对，不写
  python scripts/_sync_skill_docs.py           # 真同步（含删掉站点已没有的旧页）
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

SITE = Path(r"E:\ailearning\shenle-ai-qa\site")
DEST = Path(__file__).resolve().parent.parent / "apps" / "sut" / "backend" / "app" / "skill_docs"
DEST_ZIPS = DEST / "zips"


def sources() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for md in sorted((SITE / "kb" / "skills").glob("*.md")):
        pairs.append((md, DEST / md.name))
    for name in ("interview-api.md", "rules.md"):
        pairs.append((SITE / "kb" / name, DEST / name))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    DEST_ZIPS.mkdir(parents=True, exist_ok=True)

    pairs = sources()
    changed: list[str] = []
    for src, dst in pairs:
        if not src.exists():
            print(f"源缺失 {src}")
            continue
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            changed.append(src.name)
            if not args.check:
                shutil.copy2(src, dst)

    zips = sorted((SITE / "public" / "skills").glob("*.zip"))
    zip_changed: list[str] = []
    for src in zips:
        dst = DEST_ZIPS / src.name
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            zip_changed.append(src.name)
            if not args.check:
                shutil.copy2(src, dst)

    keep = {dst.name for _, dst in pairs}
    stale = sorted(p.name for p in DEST.glob("*.md") if p.name not in keep)
    keep_zip = {p.name for p in zips}
    stale_zip = sorted(p.name for p in DEST_ZIPS.glob("*.zip") if p.name not in keep_zip)

    print(f"手册：源 {len(pairs)} 篇，需更新 {len(changed)} 篇")
    for name in changed:
        print("  ~", name)
    print(f"zip：源 {len(zips)} 个，需更新 {len(zip_changed)} 个")
    for name in zip_changed:
        print("  ~", name)
    if stale:
        print(f"站点已没有的旧页 {len(stale)} 篇，删除：{', '.join(stale)}")
        if not args.check:
            for name in stale:
                (DEST / name).unlink()
    if stale_zip:
        print(f"站点已没有的旧 zip {len(stale_zip)} 个，删除：{', '.join(stale_zip)}")
        if not args.check:
            for name in stale_zip:
                (DEST_ZIPS / name).unlink()
    print("检查完成" if args.check else "同步完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
