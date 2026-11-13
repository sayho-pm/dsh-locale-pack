#!/usr/bin/env python3
"""npm 패키지에서 영문 사전을 뽑는다. 설치 없이 어떤 DSH 버전이든 기준선을 만들 수 있다.

    npm install --prefix <dir> @deepseek-ai/dsh@<version>
    python3 tools/extract-en-npm.py --root <dir> --out tools/en.<version>.json

extract-en.mjs는 설치된 앱 번들에서 `const en = {` 블록을 찾는데, 0.2.2-rc.2부터
번호표기가 바뀌어 같은 정규식이 한 건도 못 잡는다. 이 스크립트는 npm 패키지에
들어 있는 src/**/locales.ts 원본과 client.js의 register 호출을 대조해 네임스페이스를
복원한다.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENBLOCK = re.compile(r"export const (\w*[Ee]n)\b[^{]*\{(.*?)\n\}", re.S)
KEYVAL = re.compile(
    r"(?m)^\s*'?([A-Za-z0-9._]+)'?:\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|`((?:[^`\\]|\\.)*)`)"
)
REGISTER = re.compile(r"(?:ctx\.)?locale\.register\(\s*([^,]+?)\s*,\s*([^)]*?)\s*\)", re.S)
IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def unescape(text: str) -> str:
    return (
        text.replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\\\", "\\")
    )


def parse_en_blocks(source: str) -> dict[str, dict[str, str]]:
    """locales.ts 한 파일에서 `export const en = {…}` 들을 이름과 함께 뽑는다."""
    out: dict[str, dict[str, str]] = {}
    for name, body in ENBLOCK.findall(source):
        pairs: dict[str, str] = {}
        for m in KEYVAL.finditer(body):
            value = m.group(2) or m.group(3) or m.group(4) or ""
            if not value:
                continue
            pairs[m.group(1)] = unescape(value)
        if pairs:
            out[name] = pairs
    return out


def resolve_decl(token: str, client: str) -> str | None:
    pattern = rf"(?:const|let|var)\s+{re.escape(token)}\s*=\s*[\"'`]([^\"'`]+)[\"'`]"
    m = re.search(pattern, client)
    return m.group(1) if m else None


def object_literals(client: str) -> dict[str, dict[str, str]]:
    """client.js의 `const NAME = {…}` 리터럴에서 문자열 쌍만 뽑는다."""
    out: dict[str, dict[str, str]] = {}
    for m in re.finditer(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*\{", client):
        start = client.index("{", m.start())
        depth, in_s, esc, end = 0, None, False, -1
        for j in range(start, len(client)):
            c = client[j]
            if in_s:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == in_s:
                    in_s = None
                continue
            if c in "\"'`":
                in_s = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end < 0:
            continue
        body = client[start : end + 1]
        pairs = {}
        for km in KEYVAL.finditer(body):
            value = km.group(2) or km.group(3) or km.group(4) or ""
            if value:
                pairs[km.group(1)] = unescape(value)
        if pairs:
            out[m.group(1)] = {**out.get(m.group(1), {}), **pairs}
    return out


def registers_of(client: str) -> list[tuple[str, str]]:
    """client.js의 register 호출을 (네임스페이스, 영문 식별자) 쌍으로 뽑는다."""
    out: list[tuple[str, str]] = []
    for m in REGISTER.finditer(client):
        token = m.group(1).strip()
        body = m.group(2).strip()
        if token and token[0] in "\"'`":
            ns = token[1:-1]
        else:
            ns = resolve_decl(token, client)
        if not ns:
            continue
        if body.startswith("{"):
            ident_m = re.search(r"(?:^|,)\s*en\s*(?::\s*([A-Za-z_$][\w$]*))?\s*(?:,|$)", body)
            ident = (ident_m.group(1) if ident_m and ident_m.group(1) else "en")
        else:
            ident = body.split(",")[0].strip() or "en"
        out.append((ns, ident))
    if not out:
        single = namespace_of(client)
        if single:
            out.append((single, "en"))
    return out


def namespace_of(client: str) -> str | None:
    for pattern in (r'const NS = "([^"]+)"', r"const NS = `([^`]+)`", r'const namespace = "([^"]+)"'):
        m = re.search(pattern, client)
        if m:
            return m.group(1)
    return None


def extract(root: Path) -> dict[str, dict[str, str]]:
    pkgs = root / "node_modules" / "@deepseek-ai"
    if not pkgs.is_dir():
        raise SystemExit(f"패키지를 찾지 못했습니다: {pkgs}")

    result: dict[str, dict[str, str]] = {}
    skipped = 0
    for pkg in sorted(pkgs.iterdir()):
        if not pkg.is_dir():
            continue
        sources = [
            p
            for p in list(pkg.glob("src/**/*.ts")) + list(pkg.glob("src/*.ts"))
            if "locales" in p.name
        ]
        dicts: dict[str, dict[str, str]] = {}
        for src in sources:
            try:
                dicts.update(parse_en_blocks(src.read_text(encoding="utf-8")))
            except (OSError, UnicodeDecodeError):
                continue

        client_file = pkg / "lib" / "client.js"
        client = client_file.read_text(encoding="utf-8") if client_file.exists() else ""
        if client:
            for name, pairs in object_literals(client).items():
                dicts[name] = {**dicts.get(name, {}), **pairs}
        if not dicts:
            continue
        registers = registers_of(client)
        if not registers:
            skipped += 1
            continue

        for ns, ident in registers:
            picked = dicts.get(ident) or dicts.get("en") or dicts.get("accessDictionaries") or next(iter(dicts.values()), {})
            if not picked:
                skipped += 1
                continue
            result[ns] = {**result.get(ns, {}), **picked}

    if skipped:
        print(f"네임스페이스를 못 찾아 건너뛴 패키지 {skipped}개")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="npm install --prefix 한 디렉터리")
    ap.add_argument("--out", help="출력 파일 (기본: tools/en.<버전>.json)")
    args = ap.parse_args()

    root = Path(args.root)
    manifest = json.loads((root / "node_modules" / "@deepseek-ai" / "dsh" / "package.json").read_text(encoding="utf-8"))
    version = manifest["version"]

    data = extract(root)
    keys = sum(len(v) for v in data.values())
    out = Path(args.out) if args.out else ROOT / "tools" / f"en.{version}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"DSH {version}: 네임스페이스 {len(data)}개, 키 {keys:,}개 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
