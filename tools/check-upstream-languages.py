#!/usr/bin/env python3
"""Watch the published DeepSeek Harness locale package for new languages.

The pack covers languages DSH does not ship. When DSH starts shipping one of
them, the pack steps back rather than maintain a second copy, so this script
reports the moment the official list grows.

    python3 tools/check-upstream-languages.py           # report only
    python3 tools/check-upstream-languages.py --write    # report and record

Exit codes: 0 no change, 3 the official language list changed, 4 a newer
package appeared with the same languages.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "tools" / "upstream-languages.json"
PACKAGE = "@deepseek-ai/dsh-client-locale"


def npm(*args: str) -> str:
    return subprocess.run(
        ["npm", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def version_key(text: str) -> tuple:
    """Order 0.2.2-alpha.3 < 0.2.2-rc.1 < 0.2.2."""
    main, _, pre = text.partition("-")
    nums = [int(part) for part in re.findall(r"\d+", main)]
    if not pre:
        rank: tuple = (4,)
    else:
        label_match = re.match(r"[a-z]+", pre)
        label = label_match.group(0) if label_match else ""
        rest = [int(part) for part in re.findall(r"\d+", pre)]
        rank = ({"alpha": 1, "beta": 2, "rc": 3}.get(label, 0), *rest)
    return (*nums, *rank)


def newest_version() -> str:
    raw = npm("view", PACKAGE, "versions", "--json")
    versions = json.loads(raw) if raw.startswith("[") else [raw]
    return max(versions, key=version_key)


def official(version: str) -> dict:
    tarball = npm("view", f"{PACKAGE}@{version}", "dist.tarball")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "pkg.tgz"
        with urllib.request.urlopen(tarball, timeout=90) as response:
            archive.write_bytes(response.read())
        with tarfile.open(archive) as tar:
            names = tar.getnames()
    codes = sorted(
        Path(name).stem
        for name in names
        if "/locale/" in name and name.endswith(".json")
    )
    return {"package": PACKAGE, "version": version, "languages": codes}


def covered() -> set[str]:
    supported = json.loads((ROOT / "SUPPORTED_DSH.json").read_text(encoding="utf-8"))
    return set(supported.get("coveredLanguages") or [])


def main() -> int:
    version = newest_version()
    current = official(version)

    previous = {}
    if STATE.exists():
        previous = json.loads(STATE.read_text(encoding="utf-8"))

    old_languages = previous.get("languages", [])
    old_version = previous.get("version")
    added = [code for code in current["languages"] if code not in old_languages]
    removed = [code for code in old_languages if code not in current["languages"]]
    overlaps = sorted(set(current["languages"]) & covered())

    if added or removed:
        print(f"official language list changed in {PACKAGE} {version}")
        print(f"official: {', '.join(current['languages']) or 'none'}")
        if added:
            print(f"added: {', '.join(added)}")
            print(f"pack already covers: {', '.join(sorted(set(added) & covered())) or 'none'}")
        if removed:
            print(f"removed: {', '.join(removed)}")
        print(f"overlap with this pack: {', '.join(overlaps) or 'none'}")
        code = 3
    elif old_version and old_version != version:
        print(f"new release {PACKAGE} {old_version} → {version}")
        print(f"official languages unchanged: {', '.join(current['languages']) or 'none'}")
        code = 4
    else:
        print(
            f"no change ({version}, "
            f"{len(current['languages'])} official languages)"
        )
        code = 0

    if "--write" in sys.argv:
        STATE.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {STATE.relative_to(ROOT)}")

    return code


if __name__ == "__main__":
    raise SystemExit(main())
