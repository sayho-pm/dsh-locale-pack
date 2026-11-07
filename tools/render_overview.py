#!/usr/bin/env python3
"""Render docs/overview.html into docs/pack-overview.png.

The banner numbers are read from the repository, so the image follows the
release without hand editing.

    python3 tools/render_overview.py            # write docs/pack-overview.png
    python3 tools/render_overview.py --check    # exit 1 when the PNG is stale

Chrome's own --screenshot flag hangs on macOS when the desktop app is running,
so this drives Chromium through Playwright instead.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs" / "overview.html"
OUTPUT = ROOT / "docs" / "pack-overview.png"

WIDTH = 1600
BASE_HEIGHT = 948
GRID_START_ROWS = 6
ROW_PITCH = 35
COLUMNS = 5

NAMES = {
    "ar": "Arabic", "bn": "Bengali", "de": "German", "es": "Spanish",
    "fa": "Persian", "fr": "French", "he": "Hebrew", "hi": "Hindi",
    "id": "Indonesian", "it": "Italian", "ja": "Japanese", "ko": "Korean",
    "nl": "Dutch", "pl": "Polish", "pt": "Portuguese (PT)",
    "pt-br": "Portuguese (BR)", "ro": "Romanian", "ru": "Russian",
    "sv": "Swedish", "sw": "Swahili", "th": "Thai", "tl": "Filipino",
    "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese",
    "yo": "Yoruba", "zh-hk": "Chinese (HK)", "zh-tw": "Chinese (TW)",
}


def collect() -> dict:
    supported = json.loads((ROOT / "SUPPORTED_DSH.json").read_text(encoding="utf-8"))
    locale_dir = ROOT / "locale"
    codes = sorted(
        d.name for d in locale_dir.iterdir() if d.is_dir() and d.name != "_policy"
    )
    entries = 0
    for code in codes:
        for file in (locale_dir / code).glob("*.json"):
            entries += len(json.loads(file.read_text(encoding="utf-8")))

    rows = sorted((NAMES.get(code, code) for code in codes), key=str.casefold)
    return {
        "count": len(codes),
        "entries": entries,
        "dsh": supported["dsh"],
        "rows": rows,
    }


def build(template: str, data: dict) -> tuple[str, int]:
    rows_of_grid = -(-len(data["rows"]) // COLUMNS)
    height = BASE_HEIGHT + (rows_of_grid - GRID_START_ROWS) * ROW_PITCH
    items = "\n".join(f"      <li>{name}</li>" for name in data["rows"])
    html = (
        template.replace("{{COUNT}}", str(data["count"]))
        .replace("{{ENTRIES}}", f"{data['entries']:,}")
        .replace("{{DSH}}", data["dsh"])
        .replace("{{LANGUAGES}}", items)
        .replace("{{HEIGHT}}", str(height))
    )
    return html, height


def render(html: str, height: int, out_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    tmp = Path("/tmp") / f"overview-{abs(hash(html)) % 10**8}.html"
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": height}, device_scale_factor=1
        )
        page.goto(tmp.as_uri())
        page.wait_for_timeout(250)
        page.screenshot(path=str(out_path))
        browser.close()
    tmp.unlink(missing_ok=True)


def main() -> int:
    data = collect()
    html, height = build(TEMPLATE.read_text(encoding="utf-8"), data)
    summary = (
        f"{data['count']} languages, {data['entries']:,} entries, {data['dsh']}"
    )

    if "--check" in sys.argv:
        fresh = Path("/tmp") / "pack-overview-check.png"
        render(html, height, fresh)
        same = OUTPUT.exists() and fresh.stat().st_size == OUTPUT.stat().st_size
        fresh.unlink(missing_ok=True)
        print(
            f"pack-overview.png 최신 ({summary})"
            if same
            else "pack-overview.png이 최신 값과 다르다 — python3 tools/render_overview.py 로 다시 뽑는다"
        )
        return 0 if same else 1

    render(html, height, OUTPUT)
    print(f"wrote docs/pack-overview.png ({WIDTH}x{height}, {summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
