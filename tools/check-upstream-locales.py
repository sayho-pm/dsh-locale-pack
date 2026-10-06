#!/usr/bin/env python3
"""원문 소스와 우리 사전을 전수 대조해 누락 키를 찾는다.

DSH 저장소의 모든 locales 파일에서 영문 사전을 뽑아, 우리 baseline에 없는 문구를
찾는다. 한 건씩 찾는 대신 이 스크립트를 돌리면 전체가 한 번에 나온다.

  python3 tools/check-upstream-locales.py            # 누락만
  python3 tools/check-upstream-locales.py --refresh  # 소스 다시 받기
  python3 tools/check-upstream-locales.py --all      # 패키지별 건수까지

소스 캐시: /tmp/dsh_locales (7일 뒤 자동 정리되는 임시 폴더)
"""
import json
import os
import re
import subprocess
import sys

REPO = "deepseek-ai/deepseek-harness"
CACHE = "/tmp/dsh_locales"
BASELINE = os.path.join(os.path.dirname(__file__), "en.baseline.json")

# 어떤 export 이름이든 영문 사전 블록(en, guideEn, textEn ...)을 잡는다.
ENBLOCK = re.compile(r"export const \w*[Ee]n\b[^{]*\{(.*?)\n\}", re.S)
KEYVAL = re.compile(
    r"(?m)^\s*'?([A-Za-z0-9._]+)'?:\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")"
)


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout


def refresh() -> int:
    os.makedirs(CACHE, exist_ok=True)
    branch = sh("gh", "api", f"repos/{REPO}", "--jq", ".default_branch").strip()
    tree = sh(
        "gh", "api", f"repos/{REPO}/git/trees/{branch}?recursive=1",
        "--jq", '.tree[] | select(.path | test("locales\\\\.ts$")) | .path',
    ).split()
    for path in tree:
        out = os.path.join(CACHE, path.replace("/", "_"))
        if os.path.exists(out) and os.path.getsize(out) > 0:
            continue
        body = sh("gh", "api", f"repos/{REPO}/contents/{path}", "--jq", ".content")
        open(out, "w", encoding="utf-8").write(
            subprocess.run(["base64", "-d"], input=body, capture_output=True, text=True).stdout
        )
    return len(tree)


def source_strings() -> dict[str, list[tuple[str, str]]]:
    found: dict[str, list[tuple[str, str]]] = {}
    for fn in sorted(os.listdir(CACHE)):
        text = open(os.path.join(CACHE, fn), encoding="utf-8").read()
        for block in ENBLOCK.findall(text):
            for m in KEYVAL.finditer(block):
                val = (m.group(2) or m.group(3) or "")
                val = val.replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n")
                found.setdefault(val, []).append((fn, m.group(1)))
    return found


def package_of(filename: str) -> str:
    return filename.split("_packages_")[-1].split("_src_")[0]


def main() -> int:
    if "--refresh" in sys.argv or not os.path.isdir(CACHE):
        print(f"원문 소스를 받아옵니다: {refresh()}개 파일", flush=True)

    baseline = json.load(open(BASELINE, encoding="utf-8"))
    ours = {v for vals in baseline.values() for v in vals.values()}

    src = source_strings()
    missing = [(v, locs) for v, locs in src.items() if v not in ours]

    print(f"원문 영문 문구 {len(src)}건 | 우리 사전 {len(ours)}건")
    print(f"누락 {len(missing)}건")
    if "--all" in sys.argv or not missing:
        groups: dict[str, list] = {}
        for v, locs in missing:
            groups.setdefault(package_of(locs[0][0]), []).append((v, locs))
        for pkg in sorted(groups):
            print(f"\n■ {pkg}  ({len(groups[pkg])}건)")
            for v, locs in groups[pkg][:5]:
                print(f"    {locs[0][1]:<32} {v[:58]!r}")
            if len(groups[pkg]) > 5:
                print(f"    ... {len(groups[pkg]) - 5}건 더")
    else:
        for v, locs in missing[:20]:
            print(f"  {package_of(locs[0][0])}  {locs[0][1]:<28} {v[:50]!r}")
        if len(missing) > 20:
            print(f"  ... {len(missing) - 20}건 더 (--all 로 전체)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
