# Maintaining this pack

This file is for people who run the translation pipeline and cut releases. Users and translators do not need it; `README.md` covers installation and string edits.

## Translation pipeline

Translation runs as a separate process from any chat session. The default path is local: `tools/translate_worker.py` calls a Hy-MT2 7B server on port 18081, so no source string leaves the machine.

```bash
python3 tools/translate_worker.py --langs ja,de      # specific languages
python3 tools/translate_worker.py --all              # every language
```

`--cloud` switches to a hosted four-model chain. Use it when the local server is unavailable, when the same model keeps failing the quality gate, or when a second opinion on an official phrase is useful. Every batch records which model handled it in `번역_로그`.

Yoruba runs on the cloud chain from the start: the local model produced repeated stock phrases and left 65% of entries below the meaning threshold.

Korean runs in two passes. The first pass is the local model, the second pass re-translates the same keys on the cloud chain, then the result is scored and reviewed.

```bash
python3 tools/two_pass.py --langs ko
```

## Quality gates

```bash
npm run check-keep      # per-language rules against the English baseline
npm run build           # bundle lib/client.js from locale/
npm run smoke           # load the bundle in a JS engine and count registered entries
```

`tools/check-keep.mjs` reports five things for every language:

1. Placeholders such as `{name}` appear the same number of times as in the source
2. Product and protocol names (DeepSeek Harness, MCP, JSON, OpenAI Responses, and others) are left untranslated
3. Languages that do not use Chinese characters contain none
4. Korean sentences contain no em dashes
5. No value is empty, and no key is present that the baseline does not define

Terms that stay in English live in `locale/_policy/keep-english.json`.

## Following an upstream release

```bash
python3 tools/check-upstream-locales.py --refresh --all   # pull the newest locale sources
python3 tools/make-delta-tsv.py                           # list new and changed keys
```

Translate the delta, then run the three gates above. `SUPPORTED_DSH.json` records the upstream version, namespace count, and key count the bundle was built from.

## Releasing

1. Bump `version` in `package.json` and add a `CHANGELOG.md` section.
2. `npm run readme:sync` so the six READMEs carry the new version, key count, and bundle size. `npm run readme:check` fails when they drift.
3. Run the gates.
4. Commit, tag `v<version>`, push both the branch and the tag.
