#!/usr/bin/env python3
"""rc.5 신규 키 재작업 — Jev 0.6 미만(또는 의미 0.4 미만) 항목을 다른 모델·높은 온도로 다시 번역한다.

흐름: 대상 수집 → 원본 백업 → 재번역 → 게이트 → 재채점 → 점수가 안 오른 건 원본 복원.

사용법: python3 tools/rework_rc5.py
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)
TSV = os.path.join(ROOT, "검수용_원문대조")
OUT = os.path.join(ROOT, "검수_Jev")
LOCALE = os.path.join(BASE, "locale")
sys.path.insert(0, os.path.join(BASE, "tools"))

import translate_worker as tw  # noqa: E402

MODEL_ENTRY = tw.CHAIN[3]  # mimo-v2.6-pro (모든 티어 동일 조건의 대체 모델)
TEMP = 0.7
NEW = {
    "entryCustomization": ["install", "create", "createPrompt.sidebar",
                           "createPrompt.rightbar", "createPrompt.conversation"],
    "sidebar": ["panels.more"],
    "sidebarRight": ["tab.guide.more"],
    "conversation": ["session.moreViews"],
}
KEY_NS = {k: ns for ns, ks in NEW.items() for k in ks}


def latest_result(lang):
    best, path = -1, None
    for name in os.listdir(OUT):
        m = re.fullmatch(re.escape(lang) + r"_결과_v(\d+)\.jsonl", name)
        if m and int(m.group(1)) > best:
            best, path = int(m.group(1)), os.path.join(OUT, name)
    return path


def collect_targets():
    targets = {}
    for lang in sorted(set(KEY_NS.values()) and os.listdir(LOCALE)):
        if lang.startswith("_") or not os.path.isdir(os.path.join(LOCALE, lang)):
            continue
        path = latest_result(lang)
        if not path:
            continue
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            d = json.loads(line)
            key = d.get("key")
            if key not in KEY_NS:
                continue
            if (d.get("meaning") or 0) < 0.4 or (d.get("natural") or 0) < 0.6:
                targets.setdefault(lang, {})[key] = (d.get("meaning") or 0, d.get("natural") or 0)
    return targets


def call(prompt: str):
    provider, url, key_env, model, protocol = MODEL_ENTRY
    key = os.environ.get(key_env, "")
    if not key:
        raise SystemExit(f"missing key {key_env}")
    if protocol == "responses":
        body = json.dumps({
            "model": model,
            "instructions": "You translate desktop app UI strings. You output JSON only.",
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "temperature": TEMP,
            "max_output_tokens": 8000,
        }).encode()
    else:
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "You translate desktop app UI strings. You output JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": TEMP,
            "max_tokens": 8000,
        }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())
    if protocol == "responses":
        txt = "".join(c.get("text", "") for o in data.get("output", [])
                      for c in o.get("content", []) if isinstance(c, dict))
    else:
        txt = data["choices"][0]["message"]["content"]
    return tw.parse_json_block(txt)


def main():
    tw.load_env_keys()
    targets = collect_targets()
    total = sum(len(v) for v in targets.values())
    print(f"재작업 대상 {total}건 / {len(targets)}개 언어", flush=True)

    originals = {}
    applied = {}
    for lang, keys in sorted(targets.items()):
        batch = {}
        for key in keys:
            ns = KEY_NS[key]
            en = tw.BASELINE[ns][key]
            cur = tw.existing_keys(lang, ns).get(key, "")
            originals[f"{lang}|{ns}|{key}"] = cur
            batch[key] = en
        prompt = tw.build_prompt(lang, batch)
        prompt += "\nUse the most natural, idiomatic wording a native speaker would pick for this UI label.\n"
        out = None
        for _ in range(2):
            try:
                out = call(prompt)
            except Exception as exc:  # noqa: BLE001
                print(f"  {lang}: 호출 실패 {exc}", flush=True)
                time.sleep(3)
            if out:
                break
        if not out:
            print(f"  {lang}: 재번역 실패 → 원본 유지", flush=True)
            continue
        cand = {k: v for k, v in out.items() if k in batch and isinstance(v, str) and v.strip()}
        problems = tw.gate_batch(lang, batch, cand)
        if problems:
            bad = {p.split(":", 1)[0] for p in problems}
            cand = {k: v for k, v in cand.items() if k not in bad}
            if problems:
                print(f"  {lang}: 게이트 제외 {sorted(bad)}", flush=True)
        for key, val in cand.items():
            ns = KEY_NS[key]
            merged = tw.existing_keys(lang, ns)
            merged[key] = val
            tw.save_namespace(lang, ns, merged)
            applied[f"{lang}|{ns}|{key}"] = val
    print(f"재번역 적용 {len(applied)}건", flush=True)

    # 재채점
    for lang in sorted(targets):
        highest = -1
        for name in os.listdir(TSV):
            m = re.fullmatch(re.escape(lang) + r"_v(\d+)\.tsv", name)
            if m:
                highest = max(highest, int(m.group(1)))
        rows = []
        for ns, ks in NEW.items():
            have = tw.existing_keys(lang, ns)
            for k in ks:
                en = str(tw.BASELINE[ns][k]).replace("\t", " ").replace("\n", " ")
                tr = str(have.get(k, "")).replace("\t", " ").replace("\n", " ")
                rows.append(f"{k}\t{en}\t{tr}")
        with open(os.path.join(TSV, f"{lang}_v{highest + 1}.tsv"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        subprocess.run([sys.executable, "tools/jev_review.py", lang], cwd=BASE,
                       capture_output=True, text=True, timeout=300)

    # 점수 비교 후 복원
    restored, kept = [], []
    for lang in sorted(targets):
        old_scores = targets[lang]
        path = latest_result(lang)
        new_scores = {}
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("key") in KEY_NS:
                new_scores[d["key"]] = (d.get("meaning") or 0, d.get("natural") or 0)
        for key, (om, on) in old_scores.items():
            nm, nn = new_scores.get(key, (0, 0))
            tag = f"{lang}|{KEY_NS[key]}|{key}"
            if nm + nn > om + on:
                kept.append((lang, key, om, on, nm, nn))
            else:
                ns = KEY_NS[key]
                merged = tw.existing_keys(lang, ns)
                merged[key] = originals[tag]
                tw.save_namespace(lang, ns, merged)
                restored.append((lang, key, om, on, nm, nn))

    print(f"\n개선 적용 {len(kept)}건 / 원본 복원 {len(restored)}건", flush=True)
    print("\n--- 개선 ---")
    for lang, key, om, on, nm, nn in kept:
        print(f"  [{lang}] {key}: {om:.2f}/{on:.2f} -> {nm:.2f}/{nn:.2f}")
    print("\n--- 복원 ---")
    for lang, key, om, on, nm, nn in restored:
        print(f"  [{lang}] {key}: {om:.2f}/{on:.2f} (새 점수 {nm:.2f}/{nn:.2f})")
    with open(os.path.join(ROOT, "검수_Jev", "rc5_재작업_기록.json"), "w", encoding="utf-8") as fh:
        json.dump({"kept": kept, "restored": restored, "originals": originals},
                  fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
