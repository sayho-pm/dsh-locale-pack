#!/usr/bin/env python3
"""tok/s·tok 같은 개발자 약어를 각 언어에 맞는 표기로 바꾼다.

`tok/s` 는 국제 단위 기호가 아니라 개발자가 만든 약어라 아는 사람만 읽는다.
`ml`·`km/h` 처럼 국제 기호는 그대로 두지만, 이런 약어는 해당 언어로 옮긴다.
값에 붙는 자리이므로 숫자 뒤에 자연스럽게 읽히는 형태를 고른다.

사용법: python3 tools/fix-token-units.py [언어...]

(언어를 안 주면 한국어를 뺀 나머지 전부)
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from translate_worker import CHAIN, call_model, load_env_keys  # noqa: E402

# (파일, 키, 영어 원문)
TARGETS = [
    ("chat.json", "message.tokensPerSecond", "{tps} tok/s"),
    ("chat.json", "message.turnUsage.count", "{count} tok"),
    ("trajectory.json", "unit.tokensPerSecond", "{value} tok/s"),
    ("trajectory.json", "unit.tokens", "{value} tok"),
]

# 한국어는 손으로 정해 뒀다 (토큰/초, 토큰).
KO_FIXED = {
    "message.tokensPerSecond": "{tps} 토큰/초",
    "message.turnUsage.count": "{count} 토큰",
    "unit.tokensPerSecond": "{value} 토큰/초",
    "unit.tokens": "{value} 토큰",
}

PROMPT = """You are localizing a desktop developer tool's UI into {lang}.

Below are 4 UI strings. Each is a VALUE shown next to a number, not a label.
They use the developer abbreviations `tok/s` (tokens per second) and `tok` (tokens).
These are NOT international unit symbols like `ml` or `km/h`. They are jargon.

Use {lang}'s own word for "token" and {lang}'s own way of writing a rate:
for example German `Token/s`, Japanese `トークン/秒`, Russian `токен/с`.
Do NOT keep the English abbreviation `tok`. The slash or word order may follow
whatever reads naturally in {lang} after a number.

Keep the placeholders exactly as they are: {{tps}}, {{count}}, {{value}}.
Answer as a JSON object with exactly these 4 keys and nothing else:
{keys}
{rows}
"""


def main() -> int:
    langs = sys.argv[1:]
    if not langs:
        langs = sorted(
            d for d in os.listdir(os.path.join(ROOT, "locale"))
            if d != "_policy" and os.path.isdir(os.path.join(ROOT, "locale", d))
        )
        langs = [l for l in langs if l != "ko"]

    load_env_keys()
    total_ok = 0
    for lang in langs:
        rows = "\n".join(f"{key} = {en}" for _, key, en in TARGETS)
        keys = ", ".join(t[1] for t in TARGETS)
        prompt = PROMPT.format(lang=lang, keys=keys, rows=rows)
        out = None
        for provider, url, keyvar, model, proto in CHAIN:
            text, fail, status = call_model(provider, url, keyvar, model, proto, prompt)
            if text:
                out, used = text, model
                break
            print(f"  {lang}: {model} 실패 (fail={fail} status={status})", file=sys.stderr)
        if not out:
            print(f"{lang}: 모든 모델 실패 — 건너뜀", file=sys.stderr)
            continue

        # 모델은 JSON 객체로 답한다. 코드 블록이나 `키 = 값` 이 섞여 와도 받아들인다.
        wanted = {t[1] for t in TARGETS}
        picked = {}

        def _take(raw: dict) -> None:
            for k, v in raw.items():
                short = str(k).rsplit(".", 1)[-1]
                if not isinstance(v, str) or not v.strip():
                    continue
                if k in wanted:
                    picked[k] = v.strip()
                elif short in wanted:
                    picked[short] = v.strip()

        # 1) JSON 객체를 찾는다. 안쪽의 {tps} 같은 자리표시자 때문에 단순 정규식은
        #    안쪽 중괄호를 먼저 잡는다. 그래서 균형이 맞는 중괄호를 직접 스캔한다.
        import re as _re

        def _json_objects(text: str):
            depth, start = 0, -1
            for i, ch in enumerate(text):
                if ch == "{":
                    if depth == 0:
                        start = i
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0 and start >= 0:
                        yield text[start:i + 1]
                        start = -1

        try:
            obj = json.loads(out.strip())
            if isinstance(obj, dict):
                _take(obj)
        except (json.JSONDecodeError, ValueError):
            pass
        if not picked:
            for chunk in _json_objects(out):
                try:
                    obj = json.loads(chunk)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(obj, dict):
                    _take(obj)
        # 2) 그래도 없으면 `키 = 값` 한 줄씩
        if not picked:
            for line in out.splitlines():
                if "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip().strip('"'), v.strip().strip('"')
                if not v:
                    continue
                short = k.rsplit(".", 1)[-1]
                if k in wanted:
                    picked[k] = v
                elif short in wanted:
                    picked[short] = v

        if lang == "ko":
            picked.update(KO_FIXED)

        written = 0
        for fname, key, en in TARGETS:
            val = picked.get(key)
            if not val:
                print(f"  {lang}: {key} 값 없음 — 건너뜀", file=sys.stderr)
                continue
            if "{" in en:
                # 자리표시자가 그대로 있어야 한다
                import re
                want = set(re.findall(r"\{[a-zA-Z]+\}", en))
                got = set(re.findall(r"\{[a-zA-Z]+\}", val))
                if want != got:
                    print(f"  {lang}: {key} 자리표시자 다름 {want} != {got} — 건너뜀", file=sys.stderr)
                    continue
            p = os.path.join(ROOT, "locale", lang, fname)
            d = json.load(open(p, encoding="utf-8"))
            old = d.get(key)
            d[key] = val
            open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            written += 1
            if lang == "ko" or lang == "de":
                print(f"  {lang}.{key}: {old} → {val}")
        total_ok += written
        print(f"{lang}: {written}/4 반영 (모델 {used})")
    print(f"\n합계 {total_ok}건 반영")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
