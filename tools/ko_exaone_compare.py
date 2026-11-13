#!/usr/bin/env python3
"""한국어 델타 키를 Hy-MT2와 EXAONE 두 모델로 각각 번역해 놓고 고른 쪽을 쓴다.

    python3 tools/ko_exaone_compare.py --snapshot      # 현재 locale/ko 값을 A로 보관
    python3 tools/ko_exaone_compare.py --run           # EXAONE으로 B를 뽑아 비교·적용
    python3 tools/ko_exaone_compare.py --run --dry-run # 적용 없이 결과만

A는 --snapshot 시점에 locale/ko에 있던 값(Hy-MT2 결과), B는 EXAONE 결과다.
플레이스홀더·상품명·한자·줄표 규칙을 통과하지 못하는 쪽은 탈락시키고, 둘 다
통과하면 영문 대비 길이 비율이 한국어 평균에 가까운 쪽을 쓴다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = Path("/tmp/ko_mt2.json")
EXAONE = ("exaone", "https://api.exaone.ai/v1/chat/completions",
          "EXAONE_API_KEY", "k-exaone_v2.5", "chat_completions")


def load_worker():
    spec = importlib.util.spec_from_file_location("tw", ROOT / "tools" / "translate_worker.py")
    if spec is None or spec.loader is None:
        raise SystemExit("translate_worker를 불러오지 못했습니다")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def delta_keys(baseline: dict) -> dict[str, list[str]]:
    """이번 업데이트에서 새로 생겼거나 원문이 바뀐 키를 네임스페이스별로 뽑는다.

    이전 기준선 백업(en.baseline.<이전버전>.json.bak)과 새 기준선을 대조해 정한다.
    """
    backups = sorted(ROOT.glob("tools/en.baseline.*.json.bak"))
    if not backups:
        raise SystemExit("이전 기준선 백업을 찾지 못했습니다")
    previous = json.loads(backups[-1].read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for ns, keys in baseline.items():
        old = previous.get(ns, {})
        for key, value in keys.items():
            if key not in old or old[key] != value:
                out.setdefault(ns, []).append(key)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reuse-b", action="store_true", help="이미 뽑은 /tmp/ko_exaone.json을 쓰고, 빠진 키만 다시 호출한다")
    ap.add_argument("--pace", type=float, default=3.0, help="배치 사이 쉼 초(429 억제)")
    args = ap.parse_args()

    baseline = json.loads((ROOT / "tools" / "en.baseline.json").read_text(encoding="utf-8"))

    if args.snapshot:
        saved = {}
        for ns, keys in baseline.items():
            path = ROOT / "locale" / "ko" / f"{ns}.json"
            if not path.exists():
                continue
            have = json.loads(path.read_text(encoding="utf-8"))
            picked = {k: have[k] for k in keys if k in have}
            if picked:
                saved[ns] = picked
        SNAPSHOT.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"A(Hy-MT2) 스냅샷 {sum(len(v) for v in saved.values()):,}키 -> {SNAPSHOT}")
        return 0

    if not args.run:
        ap.error("--snapshot 또는 --run을 지정한다")

    worker = load_worker()
    worker.load_env_keys()
    worker.CHAIN[:] = [EXAONE]

    plan = delta_keys(baseline)
    if not plan:
        print("번역할 한국어 키가 없습니다")
        return 0

    out_path = Path("/tmp/ko_exaone.json")
    b: dict[str, dict[str, str]] = {}
    # plan은 비교 대상(전체 델타) 그대로 두고, 실제로 다시 부를 키만 todo로 뺀다.
    todo = plan
    if args.reuse_b and out_path.exists():
        b = json.loads(out_path.read_text(encoding="utf-8"))
        have = sum(len(v) for v in b.values())
        todo = {ns: [k for k in keys if k not in b.get(ns, {})] for ns, keys in plan.items()}
        todo = {ns: keys for ns, keys in todo.items() if keys}
        print(f"이미 뽑은 B {have:,}키, 빠진 {sum(len(v) for v in todo.values())}키만 다시 부른다")

    if todo:
        empty: dict[str, list[str]] = {}
        log = {"ok": 0, "failures": 0, "gate_failures": 0, "dropped": 0, "batches": 0}
        for ns, keys in todo.items():
            batch = {k: baseline[ns][k] for k in keys}
            for i in range(0, len(batch), 25):
                part = dict(list(batch.items())[i:i + 25])
                result = worker.translate_batch("ko", ns, part, log)
                if result:
                    b.setdefault(ns, {}).update(result)
                missing = [k for k in part if not (result and k in result)]
                if missing:
                    empty.setdefault(ns, []).extend(missing)
                if args.pace:
                    time.sleep(args.pace)
        out_path.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"B(EXAONE) {sum(len(v) for v in b.values()):,}키 -> {out_path} (실패 {sum(len(v) for v in empty.values())}키)")

    a = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if not a:
        print("A 스냅샷이 아직 없습니다(Hy-MT2가 끝난 뒤 --snapshot → --run으로 적용)")
        return 0

    ratios: list[float] = []
    for ns, keys in a.items():
        for key, value in keys.items():
            en = baseline.get(ns, {}).get(key, "")
            if en and value:
                ratios.append(len(value) / max(len(en), 1))
    typical = statistics.median(ratios) if ratios else 1.0
    print(f"한국어/영문 길이 비율 중앙값 {typical:.2f}")

    chosen_a = chosen_b = gate_fixed = no_b = 0
    examples: list[tuple[str, str, str, str]] = []
    final: dict[str, dict[str, str]] = {}
    for ns, keys in plan.items():
        target = final.setdefault(ns, {})
        for key in keys:
            en = baseline[ns][key]
            av = a.get(ns, {}).get(key)
            bv = b.get(ns, {}).get(key)
            if bv is None:
                no_b += 1
                if av is not None:
                    target[key] = av
                continue
            if av is None:
                target[key] = bv
                chosen_b += 1
                continue
            a_bad = bool(worker.gate_batch("ko", {key: en}, {key: av}))
            b_bad = bool(worker.gate_batch("ko", {key: en}, {key: bv}))
            if a_bad and not b_bad:
                target[key] = bv
                chosen_b += 1
                gate_fixed += 1
                examples.append((key, av, bv, "EXAONE 규칙 통과"))
            elif b_bad and not a_bad:
                target[key] = av
                chosen_a += 1
            else:
                a_dev = abs(len(av) / max(len(en), 1) - typical)
                b_dev = abs(len(bv) / max(len(en), 1) - typical)
                if b_dev < a_dev * 0.9:
                    target[key] = bv
                    chosen_b += 1
                    if len(examples) < 8:
                        examples.append((key, av, bv, "길이 비율이 평균에 가까움"))
                else:
                    target[key] = av
                    chosen_a += 1

    print(f"선택: Hy-MT2 {chosen_a} | EXAONE {chosen_b} (규칙 통과로 뒤집은 것 {gate_fixed}) | EXAONE 실패 {no_b}키는 Hy-MT2 유지")
    for key, av, bv, why in examples[:5]:
        print(f"  [{why}] {key}\n    MT2 : {av[:70]}\n    EXAO: {bv[:70]}")

    if args.dry_run:
        print("--dry-run: 적용하지 않았습니다")
        return 0

    for ns, values in final.items():
        path = ROOT / "locale" / "ko" / f"{ns}.json"
        have = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        have.update(values)
        path.write_text(json.dumps(have, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"locale/ko에 {sum(len(v) for v in final.values()):,}키 적용")
    return 0


if __name__ == "__main__":
    sys.exit(main())
