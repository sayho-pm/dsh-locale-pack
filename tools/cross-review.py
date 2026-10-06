#!/usr/bin/env python3
"""1차 채점에서 낮게 나온 항목을 다른 모델로 재확인한다.

Jev(판단 전용)는 점수만 주고 고쳐 쓰지 못한다. 이 스크립트는 문장 생성이 가능한
모델에 `맞음 / 틀림 + 이유 + 고친 값` 형식을 요구한다. 공급자는 이미 연결된
것 안에서만 쓴다.

사용법: python3 tools/cross-review.py <언어> [--file <tsv경로>]
"""

import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from translate_worker import CHAIN, load_env_keys, call_model  # noqa: E402
from jev_review import versioned_path  # noqa: E402

PROMPT = """You are reviewing {lang} UI translations for a desktop app.

For each pair below, answer whether the translation keeps the meaning of the English source and reads naturally as {lang} desktop UI wording.

Answer STRICTLY as one line per pair, in this format and nothing else:
번호|맞음또는틀림|이유 한 문장|고친 값 (틀림인 경우만)

번호, 세로줄, 줄바꿈을 제외한 설명을 붙이지 마세요.

{rows}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("--file", help="TSV 경로 (기본: 검수용_원문대조/<언어>.tsv)")
    args = ap.parse_args()

    load_env_keys()
    path = args.file or os.path.join(ROOT, "..", "검수용_원문대조", f"{args.lang}.tsv")
    pairs = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("##") or not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        pairs.append((parts[0], parts[1], parts[2]))

    rows = "\n".join(f"{i}. EN: {en}\n   {args.lang}: {tr}" for i, (_, en, tr) in enumerate(pairs, 1))
    prompt = PROMPT.format(lang=args.lang, rows=rows)

    for provider, url, keyvar, model, proto in CHAIN:
        try:
            out, fail, status = call_model(provider, url, keyvar, model, proto, prompt)
        except Exception as exc:
            print(f"{model}: 실패 {exc}", file=sys.stderr)
            continue
        if not out:
            print(f"{model}: 빈 응답 (fail={fail} status={status})", file=sys.stderr)
            continue
        print(f"■ 재확인 모델: {model}\n")
        out_dir = os.path.join(ROOT, "..", "검수_Jev")
        os.makedirs(out_dir, exist_ok=True)
        report_path = versioned_path(out_dir, f"{args.lang}_교차검증", "txt")
        assert not os.path.exists(report_path), f"덮어쓰기 차단: {report_path}"
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write(f"■ 재확인 모델: {model}\n\n")
            for line in out.splitlines():
                if line.strip():
                    print(line.strip())
                    fh.write(line.rstrip() + "\n")
        print(f"\n결과: {report_path}")
        return 0
    print("모든 모델이 실패했습니다", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
