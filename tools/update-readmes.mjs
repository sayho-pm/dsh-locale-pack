#!/usr/bin/env node
/**
 * README 숫자 동기화 — 릴리스마다 바뀌는 값(버전·키 수·문구 수·번들 크기)을
 * 모든 README*.md 에서 같은 값으로 맞춘다.
 *
 *   node tools/update-readmes.mjs           # 값 갱신
 *   node tools/update-readmes.mjs --check   # 어긋난 파일만 보고 (종료코드 1)
 *
 * 각 README 끝의 pack-facts 주석이 직전 값을 들고 있고, 그 문자열을 새 값으로
 * 바꾼다. 언어별 문장 구조를 몰라도 되도록 숫자 문자열만 치환한다.
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const check = process.argv.includes('--check');

const baseline = JSON.parse(readFileSync(join(root, 'tools', 'en.baseline.json'), 'utf8'));
const keys = Object.values(baseline).reduce((n, ns) => n + Object.keys(ns).length, 0);

const localeDir = join(root, 'locale');
const languages = readdirSync(localeDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith('_')).length;

let entries = 0;
for (const lang of readdirSync(localeDir, { withFileTypes: true })) {
  if (!lang.isDirectory() || lang.name.startsWith('_')) continue;
  for (const file of readdirSync(join(localeDir, lang.name))) {
    if (!file.endsWith('.json')) continue;
    entries += Object.keys(JSON.parse(readFileSync(join(localeDir, lang.name, file), 'utf8'))).length;
  }
}

const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
const supported = JSON.parse(readFileSync(join(root, 'SUPPORTED_DSH.json'), 'utf8'));
const bundleMb = (statSync(join(root, 'lib', 'client.js')).size / 1024 / 1024).toFixed(1);

const facts = {
  version: pkg.version,
  dsh: supported.dsh,
  languages: String(languages),
  keys: keys.toLocaleString('en-US'),
  entries: entries.toLocaleString('en-US'),
  bundle: `${bundleMb} MB`,
};

const BLOCK = /<!-- pack-facts:([^>]*?)-->/s;

function parseFacts(text) {
  const m = text.match(BLOCK);
  if (!m) return null;
  const out = {};
  const re = /(\w+)=("([^"]*)"|\S+)/g;
  let hit;
  while ((hit = re.exec(m[1])) !== null) {
    out[hit[1]] = hit[3] !== undefined ? hit[3] : hit[2];
  }
  return out;
}

function renderFacts(f) {
  return `<!-- pack-facts: version=${f.version} dsh=${f.dsh} languages=${f.languages} keys=${f.keys} entries=${f.entries} bundle="${f.bundle}" -->`;
}

// 문장 속에서 함께 바뀌는 표기(천 단위 구분·MB)를 그대로 치환한다.
function replaceAll(text, from, to) {
  if (!from || !to || from === to) return text;
  return text.split(from).join(to);
}

const files = readdirSync(root).filter((f) => /^README(\.[\w-]+)?\.md$/.test(f));
let stale = 0;

for (const file of files) {
  const path = join(root, file);
  const text = readFileSync(path, 'utf8');
  const old = parseFacts(text);
  if (!old) {
    console.log(`${file}: pack-facts 주석이 없다 — 추가 필요`);
    stale += 1;
    continue;
  }

  const diffs = Object.keys(facts).filter((k) => String(old[k]) !== String(facts[k]));
  if (!diffs.length) continue;

  if (check) {
    console.log(`${file}: ${diffs.map((k) => `${k} ${old[k]} → ${facts[k]}`).join(', ')}`);
    stale += 1;
    continue;
  }

  let next = text;
  for (const key of diffs) {
    // 문구 수·키 수는 본문 여러 곳에 나오므로 전부 바꾼다.
    next = replaceAll(next, old[key], facts[key]);
  }
  next = next.replace(BLOCK, renderFacts(facts));
  writeFileSync(path, next, 'utf8');
  console.log(`${file}: ${diffs.join(', ')} 갱신`);
}

if (check && stale) {
  console.log(`\nREADME ${stale}개가 최신 값과 다르다 — node tools/update-readmes.mjs 로 맞춘다`);
  process.exit(1);
}
if (!stale) console.log(`README ${files.length}개 모두 최신 (version ${facts.version}, ${facts.languages} languages, ${facts.entries} entries, ${facts.bundle})`);
