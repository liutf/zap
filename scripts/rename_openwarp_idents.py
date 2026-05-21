#!/usr/bin/env python3
"""把 Rust 源码 / 脚本 / shell 中 zap 系标识符替换为 zap 系。

只动 zap 三态:`ZAP` / `Zap` / `zap`,
不动 warp / Warp 等上游标识符。
"""
import argparse
import re
import sys
from pathlib import Path

REPLACE = [
    (re.compile(r"ZAP"), "ZAP"),
    (re.compile(r"Zap"), "Zap"),
    (re.compile(r"zap"), "zap"),
]


def transform(text: str) -> str:
    for pat, repl in REPLACE:
        text = pat.sub(repl, text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    for p in args.paths:
        path = Path(p)
        if not path.is_file():
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = transform(original)
        if original != updated:
            changed += 1
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")
    print(f"{changed} files {'would be ' if args.dry_run else ''}changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
