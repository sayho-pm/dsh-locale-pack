#!/usr/bin/env python3
"""Repair values that were written as their own key name (or contain broken chars).

The batch worker sometimes stored the key itself as the value ("Done" -> "dialog.done").
Those render as raw key names in the UI. This tool re-translates just those entries
with the local model, one key at a time, and rejects anything that still looks wrong.

    python3 tools/repair_values.py --dry-run
    python3 tools/repair_values.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fill_missing import LANG_NAMES, ENDPOINT, MODEL  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOCALE = ROOT / "locale"
BASELINE = ROOT / "tools" / "en.baseline.json"
PLACEHOLDER = re.compile(r"\{[^{}]*\}")
DASHES = ("\u2014", "\u2013", "\u2015")


def call(system: str, prompt: str, max_tokens: int) -> str:
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]


def broken(value: str, ns: str, key: str) -> bool:
    stripped = value.strip()
    return stripped in (f"{ns}.{key}", key) or "\ufffd" in value


def translate(lang: str, ns: str, key: str, source: str) -> str | None:
    language = LANG_NAMES.get(lang, lang)
    long_text = len(source) > 300 or "\n" in source
    system = (
        f"You localize software interfaces into {language}. "
        "Answer with the translation only: no quotes, no notes, no JSON, no code fences. "
        "Keep placeholders such as {name} exactly as written. "
        "Never use em dashes or en dashes."
    )
    if long_text:
        system += " Keep the markdown headings (###) and the blank lines between paragraphs."
    prompt = (
        f"{ns}.{key}\n{source}"
        if long_text
        else f"Translate this interface string: {source}"
    )
    system += " Never repeat the identifier, and never answer with the English text unchanged unless it is a proper noun."
    for _ in range(3):
        try:
            text = call(system, prompt, 2200 if long_text else 300)
        except Exception as exc:  # noqa: BLE001
            print(f"    ! {ns}.{key} 호출 실패({exc})")
            time.sleep(3)
            continue
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[A-Za-z]*\n?", "", text).rstrip("`").strip()
        if not long_text:
            text = text.split("\n")[0].strip()
            if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'":
                text = text[1:-1]
        for dash in DASHES:
            text = text.replace(f" {dash} ", ", ").replace(dash, ", ")
        if not text or "\ufffd" in text:
            continue
        if sorted(PLACEHOLDER.findall(text)) != sorted(PLACEHOLDER.findall(source)):
            continue
        if text.strip() in (f"{ns}.{key}", key):
            continue
        if len(source) > 4 and len(text) < max(2, len(source) * 0.25):
            continue
        return text
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--langs")
    args = ap.parse_args()

    baseline = json.loads(BASELINE.read_text())
    langs = sorted(p.name for p in LOCALE.iterdir() if p.is_dir() and not p.name.startswith("_"))
    if args.langs:
        keep = set(args.langs.split(","))
        langs = [l for l in langs if l in keep]

    fixed = failed = 0
    for lang in langs:
        for path in sorted((LOCALE / lang).glob("*.json")):
            ns = path.stem
            data = json.loads(path.read_text())
            targets = [k for k, v in data.items() if isinstance(v, str) and broken(v, ns, k)]
            if not targets:
                continue
            print(f"{lang}/{ns}: {len(targets)}건")
            if args.dry_run:
                continue
            for key in targets:
                source = baseline.get(ns, {}).get(key)
                if not source:
                    print(f"    ? {ns}.{key} 기준선 없음 — 건너뜀")
                    continue
                value = translate(lang, ns, key, source)
                if value is None:
                    print(f"    ✗ {ns}.{key}")
                    failed += 1
                    continue
                data[key] = value
                fixed += 1
                path.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n")
    print(f"고침 {fixed}건 / 실패 {failed}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
