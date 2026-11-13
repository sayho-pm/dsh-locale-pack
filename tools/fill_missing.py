#!/usr/bin/env python3
"""Fill keys the batch worker keeps dropping.

The batch worker asks for a JSON object of many keys at once. Some namespaces
(for example the 26-key forgePanel change block) come back with malformed JSON
on every attempt and are dropped, so those keys never reach the dictionaries.
This tool asks for one key at a time and expects plain text, which removes the
JSON parsing step entirely.

    python3 tools/fill_missing.py ko            # one language
    python3 tools/fill_missing.py --all         # every language
    python3 tools/fill_missing.py --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale"
BASELINE = ROOT / "tools" / "en.baseline.json"
ENDPOINT = "http://127.0.0.1:18081/v1/chat/completions"
MODEL = "hy-mt2-7b"

LANG_NAMES = {
    "ko": "Korean", "ja": "Japanese", "zh-tw": "Traditional Chinese (Taiwan)",
    "zh-hk": "Traditional Chinese (Hong Kong)", "es": "Spanish", "fr": "French",
    "de": "German", "pt": "Portuguese", "pt-br": "Brazilian Portuguese",
    "ru": "Russian", "ar": "Arabic", "hi": "Hindi", "th": "Thai",
    "vi": "Vietnamese", "it": "Italian", "nl": "Dutch", "pl": "Polish",
    "ro": "Romanian", "sv": "Swedish", "sw": "Swahili", "tl": "Filipino",
    "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "yo": "Yoruba",
    "bn": "Bengali", "fa": "Persian", "he": "Hebrew", "id": "Indonesian",
}

PLACEHOLDER = re.compile(r"\{[^{}]*\}")
DASHES = ("\u2014", "\u2013", "\u2015")


def call(prompt: str, system: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.2,
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"].strip()


def clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
    if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    text = text.split("\n")[0].strip()
    for dash in DASHES:
        text = text.replace(f" {dash} ", ", ").replace(dash, ", ")
    return text


def missing_keys(lang: str, baseline: dict) -> list[tuple[str, str, str]]:
    out = []
    for ns, keys in baseline.items():
        path = LOCALE / lang / f"{ns}.json"
        current = json.loads(path.read_text()) if path.exists() else {}
        for key, source in keys.items():
            if key not in current:
                out.append((ns, key, source))
    return out


def translate_one(lang: str, ns: str, key: str, source: str) -> str | None:
    language = LANG_NAMES.get(lang, lang)
    system = (
        f"You localize software user interfaces into {language}. "
        "Answer with the translation only: no quotes, no notes, no JSON. "
        "Keep every placeholder such as {name} or {base} exactly as written. "
        "Never use em dashes or en dashes; use a comma or a period instead."
    )
    prompt = f"{ns}.{key}\n{source}"
    for attempt in range(3):
        try:
            raw = call(prompt, system)
            # 모델이 프롬프트 첫 줄(네임스페이스.키)을 그대로 되돌리는 일이 있다.
            # 이 줄이 그대로 값이 되면 플레이스홀더 검사에서 전건 떨어진다(실측 9키 전부).
            lines = raw.strip().split("\n")
            if lines and lines[0].strip() in (f"{ns}.{key}", key):
                raw = "\n".join(lines[1:])
            text = clean(raw)
        except Exception as exc:  # network hiccup or model restart
            print(f"    ! {ns}.{key} 호출 실패({exc}) — 재시도")
            time.sleep(3)
            continue
        if not text:
            continue
        if sorted(PLACEHOLDER.findall(text)) != sorted(PLACEHOLDER.findall(source)):
            continue
        if any(d in text for d in DASHES):
            continue
        return text
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("languages", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    baseline = json.loads(BASELINE.read_text())
    languages = sorted(p.name for p in LOCALE.iterdir() if p.is_dir() and not p.name.startswith("_"))
    if args.languages:
        languages = [l for l in languages if l in set(args.languages)]
    elif not args.all:
        ap.error("언어를 지정하거나 --all 을 쓴다")

    total_written = 0
    for lang in languages:
        todo = missing_keys(lang, baseline)
        if not todo:
            print(f"{lang}: 빠진 키 없음")
            continue
        print(f"{lang}: {len(todo)}키 채우기")
        if args.dry_run:
            continue
        written = 0
        for ns, key, source in todo:
            value = translate_one(lang, ns, key, source)
            if value is None:
                print(f"    ✗ {ns}.{key}")
                continue
            path = LOCALE / lang / f"{ns}.json"
            data = json.loads(path.read_text()) if path.exists() else {}
            data[key] = value
            path.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n")
            written += 1
        total_written += written
        print(f"{lang}: {written}/{len(todo)} 완료")

    print(f"총 {total_written}키 기록")
    return 0


if __name__ == "__main__":
    sys.exit(main())
