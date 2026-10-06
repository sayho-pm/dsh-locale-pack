#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""바깥 실행 번역 워커 (dsh-locale-pack)

세션 모델·기억·대화와 무관하게 동작하는 별도 프로세스다. 페이로드에는 영문
UI 원문과 용어 규칙만 들어간다.

  python3 tools/translate_worker.py --langs ja,de          # 지정 언어만
  python3 tools/translate_worker.py --langs ja --ns common --limit 1   # 1배치 시험
  python3 tools/translate_worker.py --all                   # 전부

모델 사슬(계획서 3절): 실패 유형에 따라 다음 모델로 넘어간다.
  1 muse-spark-1.3-contributor   (opencode-go)
  2 meta/muse-spark-1.3-contributor (commandcode)
  3 muse-spark-1.2-contributor   (opencode-go)
  4 mimo-v2.6-pro                (opencode-go)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

ROOT = Path(__file__).resolve().parent.parent
BASELINE = json.loads((ROOT / "tools" / "en.baseline.json").read_text(encoding="utf-8"))
LOCALE_DIR = ROOT / "locale"
POLICY = json.loads((LOCALE_DIR / "_policy" / "keep-english.json").read_text(encoding="utf-8"))
LOG_DIR = Path(os.path.expanduser("~/워크스페이스/DSH_한국어플러그인/번역_로그"))

# 한국어는 사람이 정리한 사전(1,317키)이 있고, 비어 있는 나머지 키만 이 워커가 채운다(계획서 9절).
LANGS = {
    "ko": {"name": "Korean", "hint": "plain noun form for labels (요청 분석 중, 파일 읽는 중), polite 합니다체 for sentences; no Chinese characters, no em dashes"},
    "ja": {"name": "Japanese", "hint": "natural Japanese UI register; plain noun form for labels, です/ます for descriptions"},
    "zh-tw": {"name": "Traditional Chinese (Taiwan)", "hint": "Traditional Chinese characters only, never Simplified"},
    "zh-hk": {"name": "Traditional Chinese (Hong Kong)", "hint": "Traditional Chinese characters only, never Simplified; Hong Kong wording"},
    "de": {"name": "German", "hint": "German with standard capitalization of nouns"},
    "fr": {"name": "French", "hint": "French, neutral polite register"},
    "es": {"name": "Spanish", "hint": "neutral Latin American Spanish"},
    "pt-br": {"name": "Brazilian Portuguese", "hint": "Brazilian Portuguese"},
    "it": {"name": "Italian", "hint": "Italian, neutral register"},
    "nl": {"name": "Dutch", "hint": "Dutch"},
    "pl": {"name": "Polish", "hint": "Polish"},
    "ru": {"name": "Russian", "hint": "Russian, neutral register"},
    "uk": {"name": "Ukrainian", "hint": "Ukrainian, not Russian"},
    "sv": {"name": "Swedish", "hint": "Swedish"},
    "tr": {"name": "Turkish", "hint": "Turkish"},
    "id": {"name": "Indonesian", "hint": "Indonesian"},
    "vi": {"name": "Vietnamese", "hint": "Vietnamese with full diacritics"},
    "th": {"name": "Thai", "hint": "Thai"},
    "hi": {"name": "Hindi", "hint": "Hindi in Devanagari script"},
    "ar": {"name": "Arabic", "hint": "Modern Standard Arabic"},
    "tl": {"name": "Filipino (Tagalog)", "hint": "Filipino, neutral register"},
    "ro": {"name": "Romanian", "hint": "Romanian with diacritics"},
    "bn": {"name": "Bengali", "hint": "Bengali in Bengali script"},
    "ur": {"name": "Urdu", "hint": "Urdu in Nastaliq/Arabic script"},
    "he": {"name": "Hebrew", "hint": "Hebrew in Hebrew script"},
    "fa": {"name": "Persian (Farsi)", "hint": "Modern Persian in Arabic script"},
    "pt": {"name": "European Portuguese (Portugal)", "hint": "European Portuguese, not Brazilian. Prefer 2nd person (tu) or o senhor/a senhora; avoid Brazilian vocabulary and the heavy use of você. Spellings: acção, óptimo, contacto"},
    "sw": {"name": "Swahili (Kiswahili)", "hint": "Standard Kiswahili as used in Tanzanian broadcasting. Latin script. Prefer Bantu vocabulary over Arabic or English loanwords where a common Kiswahili word exists"},
    "yo": {"name": "Yorùbá", "hint": "Yorùbá in standard orthography. Every vowel carries its tone mark (à á e è é ẹ ẹ̀ ẹ́ i ì í o ò ó ọ ọ̀ ọ́ u ù ú) and the underdot letters ẹ ọ ṣ must appear where the word needs them. Never write plain e/o/s where ẹ/ọ/ṣ belongs"},
}

CJK_LANGS = {"ja", "zh-tw", "zh-hk"}
LATIN = re.compile(r"[A-Za-z]")

# 언어별 자기 문자 체계. 로마자 표기 오류를 잡는 데 쓴다.
NATIVE = {
    "ko": re.compile(r"[\uac00-\ud7a3]"),
    "ja": re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]"),
    "zh-tw": re.compile(r"[\u4e00-\u9fff]"),
    "zh-hk": re.compile(r"[\u4e00-\u9fff]"),
    "ru": re.compile(r"[\u0400-\u04ff]"),
    "uk": re.compile(r"[\u0400-\u04ff]"),
    "th": re.compile(r"[\u0e00-\u0e7f]"),
    "hi": re.compile(r"[\u0900-\u097f]"),
    "ar": re.compile(r"[\u0600-\u06ff]"),
    "ur": re.compile(r"[\u0600-\u06ff]"),
    "he": re.compile(r"[\u0590-\u05ff]"),
    "fa": re.compile(r"[\u0600-\u06ff]"),
    "bn": re.compile(r"[\u0980-\u09ff]"),
    # 요루바어는 로마자를 쓰지만 ẹ ọ ṣ 밑점과 성조 표기가 반드시 들어간다.
    "yo": re.compile(r"[ẹọṣẸỌṢàáèéìíòóùú]"),
}

CHAIN = [
    # (엔드포인트, 키 변수, 모델, 프로토콜) — OpenCode Go의 Muse Spark 계열은
    # chat/completions을 거부하고 Responses API만 받는다(ModelProtocolUnsupported).
    ("opencode-go", "https://opencode.ai/zen/go/v1/responses", "OPENCODE_GO_3WK_API_KEY", "muse-spark-1.3-contributor", "responses"),
    ("commandcode", "https://api.commandcode.ai/provider/v1/chat/completions", "COMMANDCODE_API_KEY", "meta/muse-spark-1.3-contributor", "chat"),
    ("opencode-go", "https://opencode.ai/zen/go/v1/responses", "OPENCODE_GO_3WK_API_KEY", "muse-spark-1.2-contributor", "responses"),
    ("opencode-go", "https://opencode.ai/zen/go/v1/chat/completions", "OPENCODE_GO_3WK_API_KEY", "mimo-v2.6-pro", "chat"),
]

BATCH = 25  # --batch 로 바꿀 수 있다
# OpenCode Go는 x-opencode-session 헤더가 없으면 라우팅을 거부한다(MissingSessionID).
# 안정적인 값 하나를 써서 프롬프트 캐시를 타게 한다.
SESSION_ID = "5f0d2c1a-7b3e-4c62-9a15-8d4b2f6e7c30"
UA = "dsh-locale-pack-translate/1.0 (UI localization worker)"
PLACEHOLDER = re.compile(r"\{[A-Za-z0-9_.]+\}")
CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")

# 영어로 두는 식별자. 원문에 있으면 번역문에도 있어야 한다(계획서 6절 5번).
MUST_KEEP = [
    "DeepSeek Harness", "DSH", "Cordis", "MCP", "JSON Schema", "JSONL", "JSON", "YAML",
    "CLI", "API", "URL", "SDK", "LLM", "KV Cache", "Function Calling", "TTFT",
    "OpenAI Chat Completions", "OpenAI Responses", "Anthropic Messages",
]

# 한국어 금지어(문서 규칙). 추상 표현을 구체 명사로 쓰기 위한 목록이다.
BANNED_KO = ["영역", "인사이트", "방향성", "가능성", "활용", "차원", "지점", "자리", "베팅"]

write_lock = threading.Lock()
log_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(lang: str, entry: dict) -> None:
    day = datetime.now().strftime("%Y-%m-%d")
    path = LOG_DIR / day / f"{lang}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": now_iso(), "lang": lang, **entry}
    with log_lock:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_env_keys() -> None:
    """프로필 .env에서 키를 읽는다. 값은 어디에도 남기지 않는다."""
    env_path = Path(os.path.expanduser("~/.hermes/profiles/planner/.env"))
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def call_model(provider: str, url: str, key_env: str, model: str, protocol: str, prompt: str) -> tuple[str | None, str | None, int]:
    """(본문, 실패 유형, HTTP 상태)를 돌려준다."""
    key = os.environ.get(key_env, "")
    if not key:
        return None, f"missing key {key_env}", 0
    system = "You translate desktop app UI strings. You output JSON only."
    if protocol == "responses":
        body = json.dumps({
            "model": model,
            "instructions": system,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "temperature": 0.2,
            "max_output_tokens": 16000,
        }).encode("utf-8")
    else:
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 16000,
        }).encode("utf-8")
    req = urlrequest.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": UA,
        "x-opencode-session": SESSION_ID,
    })
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        if exc.code in (429, 500, 502, 503, 504):
            return None, f"http_{exc.code}", exc.code
        return None, f"http_{exc.code}:{detail}", exc.code
    except Exception as exc:  # noqa: BLE001
        return None, f"network:{type(exc).__name__}", 0

    if protocol == "responses":
        parts = []
        for item in payload.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for part in item.get("content") or []:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    parts.append(part.get("text") or "")
        content = "".join(parts)
    else:
        try:
            content = payload["choices"][0]["message"]["content"] or ""
        except Exception:  # noqa: BLE001
            return None, "malformed_response", 200
    if not content.strip():
        return None, "empty_content", 200
    return content, None, 200


def parse_json_block(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\n", "", text)
        text = re.sub(r"\n```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:  # noqa: BLE001
        return None
    return obj if isinstance(obj, dict) else None


def build_prompt(lang_id: str, batch: dict[str, str]) -> str:
    info = LANGS[lang_id]
    terms = ", ".join(POLICY["ui"]["terms"])
    rules = [
        f"Translate the VALUES of this JSON object into {info['name']}. Keys must stay unchanged.",
        f"Language note: {info['hint']}.",
        "Keep every {placeholder} exactly as written ({name}, {count}, ...). The placeholder set of a value must not change.",
        f"Keep these terms in English, exactly as given: {terms}",
        "Values that are only symbols, units or short tokens (for example ', ', 'px', 'TTFT', '{value} ms') stay unchanged.",
        "Do not translate slash command names such as /compact or /plan.",
        "Do not use em dashes or en dashes in the translation; use other punctuation.",
        "Output only the JSON object. No code fences, no commentary, no keys other than the input keys.",
    ]
    if lang_id == "ko":
        rules.append("Avoid these Korean words: " + ", ".join(BANNED_KO))
    if lang_id in NATIVE:
        rules.append(
            "Write the translation in its own script only. Never romanize it into Latin letters. "
            "Korean must be written in Hangul, not in romanization like 'silpae' or 'Junbi jung'."
        )
    if lang_id == "ko":
        rules.append("Write Korean in Hangul. Do not use Chinese characters or Japanese kana.")
    elif lang_id not in CJK_LANGS:
        rules.append("Do not use Chinese, Japanese or Korean characters anywhere in the output.")
    else:
        rules.append("Do not use Latin script except in terms that must stay in English.")
    return "\n".join(f"{i + 1}. {r}" for i, r in enumerate(rules)) + "\n\n" + json.dumps(batch, ensure_ascii=False, indent=1)


def gate_batch(lang_id: str, src: dict[str, str], out: dict[str, object]) -> list[str]:
    problems = []
    for key, english in src.items():
        value = out.get(key)
        if not isinstance(value, str) or (not value.strip() and english.strip()):
            problems.append(f"{key}: empty")
            continue
        if sorted(PLACEHOLDER.findall(english)) != sorted(PLACEHOLDER.findall(value)):
            problems.append(f"{key}: placeholder mismatch")
        if lang_id not in CJK_LANGS and CJK.search(value):
            problems.append(f"{key}: CJK in non-CJK language")
        if lang_id == "ko":
            for word in BANNED_KO:
                if word in value:
                    problems.append(f"{key}: 금지어 {word}")
            if re.search(r"[—–]", value):
                problems.append(f"{key}: 줄표")
        native = NATIVE.get(lang_id)
        if native and value != english and LATIN.search(value) and not native.search(value):
            problems.append(f"{key}: 로마자 표기(원문과 다른데 자기 문자 없음)")
        for term in MUST_KEEP:
            if re.search(rf"(?<![A-Za-z0-9-]){re.escape(term)}(?![A-Za-z0-9-])", english):
                if term not in value:
                    problems.append(f"{key}: lost term {term}")
    return problems


def translate_batch(lang_id: str, ns: str, batch: dict[str, str], log_entries: dict) -> dict[str, str] | None:
    prompt = build_prompt(lang_id, batch)
    for index, (provider, url, key_env, model, protocol) in enumerate(CHAIN, start=1):
        attempts = 2 if index == 1 else 1
        for attempt in range(1, attempts + 1):
            content, fail_kind, status = call_model(provider, url, key_env, model, protocol, prompt)
            if content is None:
                retryable = fail_kind.startswith("http_429") or fail_kind.startswith("http_5") or fail_kind.startswith("network")
                log(lang_id, {"ns": ns, "model": model, "provider": provider, "chain": index, "attempt": attempt,
                              "status": status, "fail": fail_kind, "result": "retry" if retryable and attempt < attempts else "next_chain"})
                log_entries["failures"] += 1
                if retryable and attempt < attempts:
                    time.sleep(3 * attempt)
                    continue
                break
            parsed = parse_json_block(content)
            if parsed is None:
                log(lang_id, {"ns": ns, "model": model, "chain": index, "attempt": attempt, "fail": "json_parse", "result": "next_chain"})
                log_entries["failures"] += 1
                break
            out = {k: v for k, v in parsed.items() if k in batch}
            problems = gate_batch(lang_id, batch, out)
            if problems:
                bad = {p.split(':', 1)[0] for p in problems}
                good = {k: v for k, v in out.items() if k not in bad}
                if good:
                    # 통과한 것만 남기고 나머지는 이어서 재요청한다(부분 수용).
                    log(lang_id, {"ns": ns, "model": model, "chain": index, "attempt": attempt,
                                  "keys": len(good), "deferred": len(batch) - len(good),
                                  "fail": "gate", "problems": problems[:8], "result": "partial"})
                    log_entries["gate_failures"] += 1
                    return good
                log(lang_id, {"ns": ns, "model": model, "chain": index, "attempt": attempt,
                              "fail": "gate", "problems": problems[:8], "result": "retry"})
                log_entries["gate_failures"] += 1
                continue
            log(lang_id, {"ns": ns, "model": model, "chain": index, "attempt": attempt,
                          "keys": len(batch), "result": "ok"})
            log_entries["ok"] += 1
            return {k: out[k] for k in batch}
    return None


def existing_keys(lang_id: str, ns: str) -> dict[str, str]:
    path = LOCALE_DIR / lang_id / f"{ns}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_namespace(lang_id: str, ns: str, merged: dict[str, str]) -> None:
    path = LOCALE_DIR / lang_id / f"{ns}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def process_batch(lang_id: str, ns: str, batch: dict[str, str], log_entries: dict) -> None:
    result = translate_batch(lang_id, ns, batch, log_entries)
    if result is None:
        with write_lock:
            log_entries["dropped"] += len(batch)
        return
    with write_lock:
        merged = existing_keys(lang_id, ns)
        merged.update(result)
        save_namespace(lang_id, ns, merged)


def main() -> int:
    global BATCH
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", help="쉼표로 구분한 언어 id (예: ja,de)")
    ap.add_argument("--ns", help="네임스페이스 한 개만")
    ap.add_argument("--limit", type=int, help="언어당 배치 수 상한(시험용)")
    ap.add_argument("--all", action="store_true", help="대상 언어 전부")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--batch", type=int, help="배치 크기(기본 25). 여러 줄 값이 섞이면 줄여서 쓴다")
    args = ap.parse_args()

    load_env_keys()
    if args.batch:
        BATCH = args.batch
    if args.langs:
        lang_ids = [x.strip() for x in args.langs.split(",") if x.strip()]
    elif args.all:
        lang_ids = list(LANGS)
    else:
        ap.error("--langs 또는 --all 을 지정한다")
    for lang_id in lang_ids:
        if lang_id not in LANGS:
            ap.error(f"알 수 없는 언어 id: {lang_id}")

    namespaces = [args.ns] if args.ns else sorted(BASELINE)
    print(f"[{now_iso()}] 대상 언어 {len(lang_ids)}개, 네임스페이스 {len(namespaces)}개, 배치 크기 {BATCH}", flush=True)

    for lang_id in lang_ids:
        started = time.time()
        jobs = []
        for ns in namespaces:
            source = BASELINE[ns]
            have = existing_keys(lang_id, ns)
            # 영문이 비었거나 글자가 없는 값은 번역 없이 그대로 싣는다.
            verbatim = {k: v for k, v in source.items()
                        if k not in have and (not v.strip() or not re.search(r"[A-Za-z]", v))}
            if verbatim:
                with write_lock:
                    merged = existing_keys(lang_id, ns)
                    merged.update(verbatim)
                    save_namespace(lang_id, ns, merged)
                have = existing_keys(lang_id, ns)
            todo = {k: v for k, v in source.items() if k not in have}
            items = list(todo.items())
            for i in range(0, len(items), BATCH):
                jobs.append((ns, dict(items[i:i + BATCH])))
        if args.limit:
            jobs = jobs[: args.limit]
        if not jobs:
            print(f"{lang_id}: 이미 완료", flush=True)
            continue

        log_entries = {"ok": 0, "failures": 0, "gate_failures": 0, "dropped": 0, "batches": len(jobs)}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(process_batch, lang_id, ns, batch, log_entries) for ns, batch in jobs]
            for n, _ in enumerate(futures, start=1):
                _.result()
                if n % 10 == 0 or n == len(jobs):
                    print(f"{lang_id}: {n}/{len(jobs)} 배치 (성공 {log_entries['ok']}, 실패 {log_entries['failures']}, 게이트 {log_entries['gate_failures']})", flush=True)
        log(lang_id, {"phase": "done", "seconds": round(time.time() - started, 1), **log_entries})
        print(f"{lang_id}: 완료 ({round(time.time() - started)}초, 유실 {log_entries['dropped']}키)", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
