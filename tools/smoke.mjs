// Smoke test: load the built client bundle against a stub locale runtime
// that mirrors the real LocaleRuntime contract (addLanguage/register/bind
// with en fallback). Run: node tools/smoke.mjs
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(join(root, 'lib', 'client.js'), 'utf8');

const fail = (msg) => { throw new Error(msg); };
const expect = (cond, msg) => { if (!cond) fail(msg); };

// --- minimal ModuleLoader stub ---
let captured;
globalThis.window = { __ModuleLoader__: { load: (m) => { captured = m; } } };
(0, eval)(src);
expect(captured?.id === 'dsh-locale-pack', 'bundle id mismatch: ' + captured?.id);
const { apply, inject } = captured.factory(() => { fail('no requires expected'); });
expect(JSON.stringify(inject) === JSON.stringify(['locale']), 'inject must be ["locale"]');

// --- what the bundle claims to ship ---
const LANGS = JSON.parse(src.match(/const LANGS = (\[[\s\S]*?\n\]);/)[1]);
const DICTS = JSON.parse(src.match(/const DICTS = (\{[\s\S]*\n\});/)[1]);
expect(LANGS.length >= 2, 'bundle must ship at least 2 languages');
console.log(`bundle: ${LANGS.length} languages, ${Object.values(DICTS).reduce((n, d) => n + Object.keys(d).length, 0)} namespace registrations`);

// --- minimal locale runtime stub (en fallback like the real one) ---
const catalog = new Map([['en', { id: 'en' }]]);
const dicts = new Map([
  ['common', new Map([['en', { ok: 'OK', 'fmt.name': 'Hello {name}' }]])],
]);
const locale = {
  addLanguage: (input) => {
    if (catalog.has(input.id)) throw new Error(`locale "${input.id}" is already registered`);
    catalog.set(input.id, input);
    return () => {};
  },
  register: (ns, pairs) => {
    let m = dicts.get(ns);
    if (!m) { m = new Map(); dicts.set(ns, m); }
    for (const [l, d] of Object.entries(pairs)) {
      if (m.has(l)) throw new Error(`locale namespace "${ns}" already has locale "${l}"`);
      m.set(l, d);
    }
    return () => {};
  },
  bind: (ns) => (key, params) => {
    for (const l of ['ja', 'ko', 'en']) {
      const v = dicts.get(ns)?.get(l)?.[key];
      if (v !== undefined) return params ? v.replace(/\{(\w+)\}/g, (mm, n) => (n in params ? String(params[n]) : mm)) : v;
    }
    return key;
  },
};

const ctx = { effect: (fn) => fn(), locale };
apply(ctx);

// Dictionaries register after boot in deferred chunks (the web client has a
// finite activation budget), so the assertions below wait for the queue to drain.
const flushRegistration = async (maxTicks = 6000) => {
  let last = -1;
  let stable = 0;
  for (let i = 0; i < maxTicks; i += 1) {
    const count = [...dicts.values()].reduce((n, m) => n + m.size, 0);
    if (count === last) {
      stable += 1;
      if (stable > 5) return;
    } else {
      stable = 0;
      last = count;
    }
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  fail('deferred dictionary registration did not settle');
};
await flushRegistration();

// 1. every language in the bundle is registered with an en fallback
for (const { id, label } of LANGS) {
  const entry = catalog.get(id);
  expect(entry, `language ${id} was not registered`);
  expect(entry.label === label, `language ${id} label mismatch`);
  expect(entry.fallback === 'en', `language ${id} must fall back to en`);
}

// 2. every namespace of every language landed in the runtime
for (const [lang, namespaces] of Object.entries(DICTS)) {
  for (const ns of Object.keys(namespaces)) {
    expect(dicts.get(ns)?.get(lang), `${lang}/${ns} was not registered`);
    expect(Object.keys(dicts.get(ns).get(lang)).length > 0, `${lang}/${ns} is empty`);
  }
}

// 3. lookup falls back to English for keys a language does not carry
const bind = locale.bind('common');
expect(bind('ok') === 'OK', 'en fallback lookup failed');
expect(bind('fmt.name', { name: 'Ana' }) === 'Hello Ana', 'param substitution failed');

// 4. double load is idempotent (duplicate registration is swallowed)
apply(ctx);
console.log('double-load OK (idempotent)');

// 5. the locale font sheet travels with the bundle, one rule per corrected locale
const FONT_CSS = JSON.parse(src.match(/const FONT_CSS = (".*?");\n/)[1]);
const EXPECTED_STACKS = {
  ja: { keep: ['"Hiragino Sans"', '"Yu Gothic"', 'Meiryo'], drop: ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei'] },
  'zh-tw': { keep: ['"PingFang TC"', '"Microsoft JhengHei"'], drop: ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei'] },
  'zh-hk': { keep: ['"PingFang HK"', '"PingFang TC"', '"Microsoft JhengHei"'], drop: ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei'] },
};
for (const [id, spec] of Object.entries(EXPECTED_STACKS)) {
  const start = FONT_CSS.indexOf(`html[lang="${id}"]`);
  expect(start >= 0, `font sheet has no rule for ${id}`);
  const next = FONT_CSS.slice(start + 1).indexOf('html[lang="');
  const rule = FONT_CSS.slice(start, next >= 0 ? start + 1 + next : FONT_CSS.length);
  for (const face of spec.keep) expect(rule.includes(face), `${id} stack must keep ${face}`);
  for (const face of spec.drop) expect(!rule.includes(face), `${id} stack must drop ${face}`);
}
expect(FONT_CSS.includes('--ds-font-family-code'), 'code stack needs the same correction');

// 6. the sheet is attached once and survives a double load
const attached = new Map();
globalThis.document = {
  head: { appendChild: (el) => attached.set(el.id, el) },
  createElement: () => ({ id: '', textContent: '', remove() { attached.delete(this.id); } }),
  getElementById: (id) => attached.get(id) ?? null,
};
apply(ctx);
expect(attached.has('dsh-locale-pack-fonts'), 'font sheet was not attached');
expect(attached.get('dsh-locale-pack-fonts').textContent.includes('html[lang="ja"]'), 'attached sheet lacks the ja rule');
apply(ctx);
expect(attached.size === 1, 'double load duplicated or dropped the font sheet');
delete globalThis.document;
console.log('font sheet OK (single attach, double-load safe)');

// 7. plugin display text: locale/<lang>.json carries a non-empty description per language
const LANGUAGE_ID = /^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$/;
const metaDir = join(root, 'locale');
const metaFiles = readdirSync(metaDir).filter((f) => f.endsWith('.json'));
expect(metaFiles.includes('en.json'), 'locale/en.json anchors the plugin display text');
for (const f of metaFiles) expect(LANGUAGE_ID.test(f.slice(0, -5)), `locale/${f} must use a language id as its filename`);
for (const { id } of LANGS) {
  const file = metaFiles.find((f) => f.slice(0, -5).toLowerCase() === id.toLowerCase());
  expect(file, `locale/${id}.json is missing`);
  const desc = JSON.parse(readFileSync(join(metaDir, file), 'utf8')).meta?.description;
  expect(typeof desc === 'string' && desc.trim().length > 0, `locale/${file}: meta.description must be a non-empty string`);
}
console.log(`plugin description OK (${metaFiles.length} locale files)`);

// 8. the manifest must export the display-text files, or the app silently falls
// back to the package.json description for every language
const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
expect(manifest.exports?.['./locale/*.json'] === './locale/*.json', 'package.json must export ./locale/*.json or the display text is never read');
expect(typeof manifest.description === 'string' && manifest.description.trim().length > 0, 'package.json description is the fallback display text');

console.log(`smoke OK — ${LANGS.length} languages verified`);
