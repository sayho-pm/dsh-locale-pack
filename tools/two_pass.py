#!/usr/bin/env python3
"""한국어 2단계 번역 — 로컬 Hy-MT2 1차 → 클라우드 사슬 2차.

2026-11-07 세호 지시: 한국어는 MT2로 초안을 뽑은 뒤 같은 키를 클라우드 사슬로
다시 번역한다. 1차 값은 비교용으로 tar 백업에 남긴다.

  python3 tools/two_pass.py --langs ko
  python3 tools/two_pass.py --langs ko --dry-run

실행 전에 클라우드 사슬 키를 환경에 올린다:
  set -a; source ~/.hermes/profiles/planner/.env; set +a
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tarfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale"
BASE = json.loads((ROOT / "tools" / "en.baseline.json").read_text(encoding="utf-8"))


def pending(lang: str) -> list[tuple[str, str]]:
    """(네임스페이스, 키) 목록 — 값이 비었거나 공백뿐인 자리."""
    out = []
    for ns, keys in BASE.items():
        path = LOCALE / lang / f"{ns}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        for key in keys:
            source = keys[key]
            if not source.strip():
                continue  # 빈 문자열·공백 구분자는 번역 대상이 아니다
            value = data.get(key)
            if not (isinstance(value, str) and value.strip()):
                out.append((ns, key))
    return out


def drop(lang: str, targets: list[tuple[str, str]]) -> int:
    removed = 0
    for ns in {ns for ns, _ in targets}:
        path = LOCALE / lang / f"{ns}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        before = len(data)
        for key in [k for n, k in targets if n == ns]:
            data.pop(key, None)
        if len(data) != before:
            removed += before - len(data)
            path.write_text(
                json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return removed


def run_worker(lang: str, args: argparse.Namespace, cloud: bool) -> int:
    cmd = [sys.executable, str(ROOT / "tools" / "translate_worker.py"),
           "--langs", lang, "--batch", str(args.batch), "--workers", str(args.workers)]
    if cloud:
        cmd.append("--cloud")
    print(f"\n=== {'2차 클라우드' if cloud else '1차 로컬 MT2'} ===", flush=True)
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="ko")
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for lang in [x.strip() for x in args.langs.split(",") if x.strip()]:
        todo = pending(lang)
        print(f"[{lang}] 대상 {len(todo)}키", flush=True)
        if not todo:
            print(f"[{lang}] 빈 자리가 없다 — 2차만 돌리려면 값을 먼저 지운다", flush=True)
            continue
        if args.dry_run:
            continue

        stamp = time.strftime("%Y%m%d_%H%M")
        backup = ROOT.parent / f"locale_{lang}_mt2_{stamp}.tgz"
        with tarfile.open(backup, "w:gz") as tar:
            tar.add(LOCALE / lang, arcname=f"locale/{lang}")
        print(f"[{lang}] 1차 값 백업 → {backup.name}", flush=True)

        if run_worker(lang, args, cloud=False) != 0:
            print(f"[{lang}] 1차 실패 — 2차로 넘어가지 않는다", flush=True)
            continue

        left = pending(lang)
        filled = len(todo) - len(left)
        print(f"[{lang}] 1차 채움 {filled}키, 남음 {len(left)}키", flush=True)
        if filled == 0:
            print(f"[{lang}] 1차가 아무것도 채우지 못했다", flush=True)
            continue

        removed = drop(lang, todo)
        print(f"[{lang}] 2차를 위해 {removed}키 삭제", flush=True)

        if run_worker(lang, args, cloud=True) != 0:
            print(f"[{lang}] 2차 실패 — 1차 값은 {backup.name} 에 있다", flush=True)
            continue

        left = pending(lang)
        print(f"[{lang}] 완료 — 남은 빈 자리 {len(left)}키", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
