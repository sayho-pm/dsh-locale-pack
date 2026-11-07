#!/usr/bin/env python3
"""이번 업데이트에서 새로 넣거나 원문이 바뀐 키만 원문 대조표로 뽑는다.

전체 사전(4,016키 × 29언어)을 채점하면 이번에 손대지 않은 3,000여 키까지 다시
점수를 매기게 된다. 범위를 업데이트 델타로 좁히기 위한 표를 만든다.

줄 형식: 키 \\t 영문 원문 \\t 번역   (탭·줄바꿈은 공백으로 눌러 한 줄에 한 쌍)
출력: ../검수용_원문대조/<언어>_delta.tsv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "검수용_원문대조"
LOCALE = ROOT / "locale"


def flat(data: dict) -> dict[str, str]:
    return {f"{ns}.{k}": v for ns, keys in data.items() for k, v in keys.items()}


def main() -> int:
    union = flat(json.loads((ROOT / "tools" / "en.baseline.json").read_text()))
    rc5 = flat(json.loads((ROOT / "tools" / "en.0.2.1-rc.5.json").read_text()))
    delta = (set(union) - set(rc5)) | {k for k in set(union) & set(rc5) if union[k] != rc5[k]}
    print(f"업데이트 델타 {len(delta):,}키")
    OUT.mkdir(exist_ok=True)
    langs = sorted(p.name for p in LOCALE.iterdir() if p.is_dir() and not p.name.startswith("_"))
    rows = 0
    for lang in langs:
        have: dict[str, str] = {}
        for path in sorted((LOCALE / lang).glob("*.json")):
            ns = path.stem
            for k, v in json.loads(path.read_text()).items():
                have[f"{ns}.{k}"] = v
        lines = []
        for key in sorted(delta):
            value = have.get(key)
            if value is None:
                continue
            en = " ".join(union[key].split())
            tr = " ".join(value.split())
            lines.append(f"{key}\t{en}\t{tr}")
        (OUT / f"{lang}_delta.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        rows += len(lines)
        print(f"  {lang}: {len(lines)}행")
    print(f"합계 {rows:,}행 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
