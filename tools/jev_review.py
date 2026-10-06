#!/usr/bin/env python3
"""Jev 판단 모델로 번역 검수 (dsh-locale-pack).

원문 대조표의 줄을 10개씩 묶어 Jev에 물어보고, 의미·자연스러움 점수를 받는다.
Jev는 문구를 고쳐 쓰지 못하므로 잘못된 값을 골라 내는 용도로만 쓴다.

사용법: python3 tools/jev_review.py <언어코드> [--limit N]
결과: 검수_Jev/<언어코드>_결과.jsonl, 검수_Jev/<언어코드>_요약.md
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TSV = os.path.join(BASE, "검수용_원문대조")
OUT = os.path.join(BASE, "검수_Jev")
URL = "https://api.commandcode.ai/provider/v1/systemone"
MODEL = "typesafe/jev"
BATCH = 10
WORKERS = 8
WARN = 0.6   # 이 아래는 사람이 다시 봄
BAD = 0.4    # 이 아래는 잘못된 번역으로 봄

TONE = {
    "ja": "Japanese desktop app UI for developers",
    "de": "German desktop app UI for developers",
    "fr": "French desktop app UI for developers",
    "es": "Spanish desktop app UI for developers",
    "pt-br": "Brazilian Portuguese desktop app UI for developers",
    "it": "Italian desktop app UI for developers",
    "nl": "Dutch desktop app UI for developers",
    "pl": "Polish desktop app UI for developers",
    "ru": "Russian desktop app UI for developers",
    "uk": "Ukrainian desktop app UI for developers",
    "sv": "Swedish desktop app UI for developers",
    "tr": "Turkish desktop app UI for developers",
    "id": "Indonesian desktop app UI for developers",
    "vi": "Vietnamese desktop app UI for developers",
    "th": "Thai desktop app UI for developers",
    "hi": "Hindi desktop app UI for developers",
    "ar": "Arabic desktop app UI for developers",
    "tl": "Filipino desktop app UI for developers",
    "ro": "Romanian desktop app UI for developers",
    "bn": "Bengali desktop app UI for developers",
    "ur": "Urdu desktop app UI for developers",
    "he": "Hebrew desktop app UI for developers",
    "fa": "Persian desktop app UI for developers",
    "pt": "European Portuguese (Portugal) desktop app UI for developers",
    "sw": "Swahili desktop app UI for developers",
    "yo": "Yorùbá desktop app UI for developers",
}


def load_key():
    path = os.path.expanduser("~/.hermes/profiles/planner/.env")
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("COMMANDCODE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("COMMANDCODE_API_KEY를 찾을 수 없습니다")


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def read_tsv(lang, limit=None):
    rows = []
    # 최신 버전 대조표를 읽는다. 이전 버전은 남아 있으므로 보존된다.
    import re as _re
    latest, highest = None, -1
    for name in os.listdir(TSV) if os.path.isdir(TSV) else []:
        m = _re.fullmatch(_re.escape(lang) + r"_v(\d+)\.tsv", name)
        if m and int(m.group(1)) > highest:
            highest, latest = int(m.group(1)), name
    if latest is None:
        latest = f"{lang}.tsv"  # 버저닝 이전 파일
    for line in open(os.path.join(TSV, latest), encoding="utf-8"):
        if line.startswith("##") or not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        rows.append((parts[0], parts[1], parts[2]))
    return rows[:limit] if limit else rows


def ask(rows, lang):
    state = []
    questions = {}
    tone = TONE.get(lang, f"{lang} desktop app UI for developers")
    for i, (key, en, tr) in enumerate(rows, 1):
        state.append(f"{i}. EN: {en}\n   {lang}: {tr}")
        questions[f"m{i}"] = {
            "type": "noul",
            "instructions": f"Does pair {i} keep the meaning of the English source? Answer as a confidence score.",
        }
        questions[f"n{i}"] = {
            "type": "noul",
            "instructions": f"Is pair {i} natural {tone} wording? Answer as a confidence score.",
        }
    body = {"model": MODEL, "state": "\n".join(state), "questions": questions}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=HEADERS)
    for attempt in range(3):
        try:
            out = json.load(urllib.request.urlopen(req, timeout=60))
            return out.get("answers", {})
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(2 + attempt * 3)
                continue
            raise
        except Exception:
            if attempt < 2:
                time.sleep(2)
                continue
            raise
    return {}


def score(answer):
    if isinstance(answer, dict) and "noul" in answer:
        try:
            return float(answer["noul"])
        except (TypeError, ValueError):
            return None
    return None


def versioned_path(out_dir: str, stem: str, ext: str) -> str:
    """덮어쓰지 않고 다음 버전 파일 경로를 돌려준다.

    같은 이름을 다시 쓰면 이전 채점 기록이 사라진다(2026-10-06 실측: 재검수
    재시도가 원본 채점 파일을 지워 7,581줄이 날아갔다). 그래서 기존 파일을
    절대 덮지 않고 번호를 하나 올린다: `<stem>_v1.<ext>`, `<stem>_v2.<ext>`, ...
    """
    import re as _re
    highest = 0
    for name in os.listdir(out_dir) if os.path.isdir(out_dir) else []:
        m = _re.fullmatch(_re.escape(stem) + r"_v(\d+)\." + _re.escape(ext), name)
        if m:
            highest = max(highest, int(m.group(1)))
    return os.path.join(out_dir, f"{stem}_v{highest + 1}.{ext}")


def main():
    lang = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    key = load_key()
    HEADERS["Authorization"] = f"Bearer {key}"
    rows = read_tsv(lang, limit)
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    os.makedirs(OUT, exist_ok=True)
    result_path = versioned_path(OUT, f"{lang}_결과", "jsonl")
    assert not os.path.exists(result_path), f"덮어쓰기 차단: {result_path}"
    print(f"{lang}: {len(rows)}줄, {len(batches)}배치, 배치 크기 {BATCH}")
    done = 0
    with open(result_path, "w", encoding="utf-8") as fh:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            results = ex.map(lambda b: ask(b, lang), batches)
            for bi, answers in enumerate(results, 1):
                for j, (key_id, en, tr) in enumerate(batches[bi - 1], 1):
                    m = score(answers.get(f"m{j}"))
                    n = score(answers.get(f"n{j}"))
                    fh.write(json.dumps({"key": key_id, "en": en, "tr": tr, "meaning": m, "natural": n}, ensure_ascii=False) + "\n")
                if bi % 20 == 0:
                    print(f"  {bi}/{len(batches)} 배치")
    print(f"결과: {result_path}")


if __name__ == "__main__":
    main()
