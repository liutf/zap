#!/usr/bin/env python3
"""一次性脚本:把 Zap 项目里需要改名的字符串从 Warp 系替换成 Zap。

策略:
- 用占位符保护不可改动的 token(`warp.dev` URL、`Warpify*` 系列技术词、env var、
  路径/标识符内部的 warp_ 等)。
- 替换核心品牌词:`Warp Drive`、`WarpDrive`、`Zap`、独立 `Warp`、独立 `warp`。
- 还原占位符。

只覆盖 i18n .ftl + 用户可见的 markdown / 顶层 hbs / about.toml,以及指定的少量源代码字符串。
"""
import argparse
import re
import sys
from pathlib import Path

# (pattern, placeholder) — 在主替换前替换为占位符,主替换完后再换回。
# 占位符只用不包含 WARP / warp / Warp 的字符,避免嵌套化。
PROTECT = [
    # URLs / domains 保留 (warp.dev 是真实 upstream URL)
    (re.compile(r"app\.warp\.dev"), "\x00DOMAIN1\x00"),
    (re.compile(r"warp\.dev"), "\x00DOMAIN2\x00"),
    (re.compile(r"warpdotdev"), "\x00DOMAIN3\x00"),
    # 技术词:Warpify / Warpification / Warpified
    (re.compile(r"Warpification"), "\x00TECH1\x00"),
    (re.compile(r"Warpified"), "\x00TECH2\x00"),
    (re.compile(r"Warpify"), "\x00TECH3\x00"),
    (re.compile(r"warpification"), "\x00TECH4\x00"),
    (re.compile(r"warpified"), "\x00TECH5\x00"),
    (re.compile(r"warpify"), "\x00TECH6\x00"),
    # 环境变量 / 配置 key
    (re.compile(r"WARP_"), "\x00ENV1\x00"),
    (re.compile(r"\bwarp\.pty\.recording\b"), "\x00CFG1\x00"),
    # 内部标识符 warp_ 开头 (snake_case ident,通常 Rust 用)
    (re.compile(r"\bwarp_([a-zA-Z0-9_]+)"), "\x00ID1_\\1\x00"),
    # WarpUI 框架名(MIT license,内部框架,保留)
    (re.compile(r"WarpUI"), "\x00UI1\x00"),
    (re.compile(r"warpui"), "\x00UI2\x00"),
]

# 主替换 — 按特异性从高到低排序
REPLACE = [
    # bin / artifact 名
    (re.compile(r"\bwarp-oss\b"), "zap-oss"),
    (re.compile(r"\bZap\b"), "Zap"),
    (re.compile(r"\bzap\b"), "zap"),
    (re.compile(r"\bWarp Drive\b"), "Zap"),
    (re.compile(r"\bWarpDrive\b"), "Zap"),
    (re.compile(r"\bwarp drive\b"), "zap"),
    # Get Warping → Get Zapping (slogan)
    (re.compile(r"\bGet Warping\b"), "Get Zapping"),
    (re.compile(r"\bget warping\b"), "get zapping"),
    # Bare brand
    (re.compile(r"\bWarp\b"), "Zap"),
]

# 注意:不替换裸 lowercase `warp` —— 太多技术上下文(`use warp::*`, file `warp.ftl`,
# `warp-channel-config` 等)。如果某些 i18n 行有 lowercase `warp` 需要改,
# 由后续手工处理。

RESTORE = [
    ("\x00DOMAIN1\x00", "app.warp.dev"),
    ("\x00DOMAIN2\x00", "warp.dev"),
    ("\x00DOMAIN3\x00", "warpdotdev"),
    ("\x00TECH1\x00", "Warpification"),
    ("\x00TECH2\x00", "Warpified"),
    ("\x00TECH3\x00", "Warpify"),
    ("\x00TECH4\x00", "warpification"),
    ("\x00TECH5\x00", "warpified"),
    ("\x00TECH6\x00", "warpify"),
    ("\x00ENV1\x00", "WARP_"),
    ("\x00CFG1\x00", "warp.pty.recording"),
    ("\x00UI1\x00", "WarpUI"),
    ("\x00UI2\x00", "warpui"),
]
RESTORE_WARP_IDENT = re.compile("\x00ID1_([a-zA-Z0-9_]+)\x00")


def transform(text: str) -> str:
    for pat, ph in PROTECT:
        text = pat.sub(ph, text)
    for pat, repl in REPLACE:
        text = pat.sub(repl, text)
    for ph, original in RESTORE:
        text = text.replace(ph, original)
    text = RESTORE_WARP_IDENT.sub(r"warp_\1", text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="files to transform in-place")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    for p in args.paths:
        path = Path(p)
        if not path.is_file():
            print(f"skip (not a file): {p}", file=sys.stderr)
            continue
        original = path.read_text(encoding="utf-8")
        updated = transform(original)
        if original != updated:
            changed += 1
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")
            diff_count = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
            print(f"{'would change' if args.dry_run else 'changed'}: {p} (~{diff_count} lines)")
        else:
            print(f"no-change: {p}")
    print(f"\n{changed} files {'would be ' if args.dry_run else ''}changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
