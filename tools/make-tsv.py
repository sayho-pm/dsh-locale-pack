#!/usr/bin/env python3
"""원문 대조표(TSV) 만들기 — Jev 검수 입력.

각 언어마다 `검수용_원문대조/<언어>.tsv`를 만든다.
줄 형식: 키 \t 영문 원문 \t 번역

사용법: python3 tools/make-tsv.py [언어코드 ...]
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)  # 검수 자료는 저장소 밖 DSH_한국어플러그인/ 에 둔다
OUT = os.path.join(ROOT, "검수용_원문대조")
LOCALE = os.path.join(BASE, "locale")
sys.path.insert(0, os.path.join(BASE, "tools"))
from jev_review import versioned_path  # noqa: E402


def main():
    langs = sys.argv[1:]
    if not langs:
        langs = sorted(
            d
            for d in os.listdir(LOCALE)
            if d != "_policy" and os.path.isdir(os.path.join(LOCALE, d))
        )
    os.makedirs(OUT, exist_ok=True)

    baseline_path = os.path.join(BASE, "tools", "en.baseline.json")
    baseline = json.load(open(baseline_path, encoding="utf-8"))

    for lang in langs:
        rows = []
        for ns, source in baseline.items():
            path = os.path.join(LOCALE, lang, f"{ns}.json")
            have = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
            for key, en in source.items():
                tr = have.get(key)
                if tr is None or tr == "":
                    continue
                # 탭과 줄바꿈은 TSV를 깨뜨리므로 공백으로 눌러 둔다.
                en_clean = str(en).replace("\t", " ").replace("\n", " ").replace("\r", " ")
                tr_clean = str(tr).replace("\t", " ").replace("\n", " ").replace("\r", " ")
                rows.append(f"{ns}.{key}\t{en_clean}\t{tr_clean}")

        path = versioned_path(OUT, lang, "tsv")
        assert not os.path.exists(path), f"덮어쓰기 차단: {path}"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"## {lang} {len(rows)} rows\n")
            fh.write("## key\tenglish\ttranslation\n")
            fh.write("\n".join(rows) + "\n")
        print(f"{lang}: {len(rows)}줄 → {path}")


if __name__ == "__main__":
    main()
