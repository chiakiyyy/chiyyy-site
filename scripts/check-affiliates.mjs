#!/usr/bin/env node
/**
 * アフィリエイト案件の定期点検スクリプト（依存なし / Node 18以上）
 *
 *   node scripts/check-affiliates.mjs           … オフライン点検のみ
 *   node scripts/check-affiliates.mjs --fetch    … リンク到達性もチェック
 *
 * 見るもの:
 *   1. 案件マスタの必須項目・URLの差し替え漏れ
 *   2. 終了日を過ぎた案件 / 30日以内に終了する案件
 *   3. 記事が参照している案件IDがマスタに存在するか
 *   4. マスタにあるが1記事も使っていない案件
 *   5. affiliates を持つ記事に pr: true があるか（広告表記漏れ）
 *   6. --fetch 時: URLがリンク切れしていないか
 */

import { readFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MASTER = path.join(ROOT, 'src/data/affiliates.json');
const POSTS_DIR = path.join(ROOT, 'src/content/blog');
const DO_FETCH = process.argv.includes('--fetch');
const SOON_DAYS = 30;

const errors = [];
const warns = [];
const infos = [];

const jstToday = () =>
  new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);

const addDays = (iso, n) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};

/* ---------- 1. 案件マスタ ---------- */

let master;
try {
  master = JSON.parse(await readFile(MASTER, 'utf8'));
} catch (e) {
  console.error(`案件マスタを読めません: ${MASTER}\n${e.message}`);
  process.exit(1);
}

const today = jstToday();
const soonLimit = addDays(today, SOON_DAYS);
const VALID_STATUS = ['active', 'paused', 'ended'];

for (const [id, item] of Object.entries(master)) {
  const at = (msg) => `${id}: ${msg}`;

  if (!item.label) errors.push(at('label が空です'));
  if (!VALID_STATUS.includes(item.status))
    errors.push(at(`status が不正です（${item.status}）`));

  if (item.status === 'active') {
    if (!item.url) errors.push(at('掲載中なのに url が空です'));
    if (item.url && /REPLACE_ME|example\.(com|net)/.test(item.url))
      errors.push(at('url がサンプルのままです。実リンクに差し替えてください'));
  }

  if (item.endsAt) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(item.endsAt)) {
      errors.push(at(`endsAt の書式が不正です（${item.endsAt}）`));
    } else if (item.endsAt < today && item.status === 'active') {
      errors.push(
        at(`終了日(${item.endsAt})を過ぎています。status を ended にしてください`)
      );
    } else if (item.endsAt <= soonLimit && item.status === 'active') {
      warns.push(at(`${item.endsAt} に終了予定です（残り${SOON_DAYS}日以内）`));
    }
  }

  if (item.status !== 'active' && !item.fallbackUrl) {
    warns.push(
      at('停止/終了しているのに fallbackUrl が未設定です（本文のリンクが消えます）')
    );
  }
}

/* ---------- 2. 記事側の参照 ---------- */

const usedIds = new Set();

/** frontmatter から pr と affiliates だけを素朴に取り出す */
function parseFrontmatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return null;
  const body = m[1];
  const pr = /^pr:\s*true\s*$/m.test(body);
  const affiliates = [];
  const listMatch = body.match(/^affiliates:\s*\r?\n((?:\s*-\s*.+\r?\n?)+)/m);
  if (listMatch) {
    for (const line of listMatch[1].split(/\r?\n/)) {
      const v = line.match(/^\s*-\s*['"]?([^'"\s]+)['"]?\s*$/);
      if (v) affiliates.push(v[1]);
    }
  }
  const inline = body.match(/^affiliates:\s*\[([^\]]*)\]/m);
  if (inline) {
    for (const v of inline[1].split(',')) {
      const t = v.trim().replace(/^['"]|['"]$/g, '');
      if (t) affiliates.push(t);
    }
  }
  return { pr, affiliates };
}

async function walk(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(p)));
    else if (/\.mdx?$/.test(e.name)) out.push(p);
  }
  return out;
}

if (existsSync(POSTS_DIR)) {
  const files = await walk(POSTS_DIR);
  for (const file of files) {
    const rel = path.relative(ROOT, file);
    const src = await readFile(file, 'utf8');
    const fm = parseFrontmatter(src);

    // .mdx で <AffLink id="..."> を直書きしている分も拾う
    const inlineIds = [...src.matchAll(/<Aff(?:Link|Card)\s+[^>]*id=["']([^"']+)["']/g)]
      .map((m) => m[1]);

    const ids = [...new Set([...(fm?.affiliates ?? []), ...inlineIds])];
    ids.forEach((id) => usedIds.add(id));

    for (const id of ids) {
      if (!master[id]) errors.push(`${rel}: 未登録の案件ID "${id}" を参照しています`);
    }

    if (ids.length > 0 && fm && !fm.pr) {
      warns.push(`${rel}: 案件を掲載していますが pr: true がありません（広告表記漏れ）`);
    }
  }
  infos.push(`記事 ${files.length} 件を走査しました`);
} else {
  warns.push(`記事ディレクトリが見つかりません: ${path.relative(ROOT, POSTS_DIR)}`);
}

for (const [id, item] of Object.entries(master)) {
  if (item.status === 'active' && !usedIds.has(id)) {
    infos.push(`${id}: どの記事にも掲載されていません`);
  }
}

/* ---------- 3. リンク到達性 ---------- */

if (DO_FETCH) {
  const targets = Object.entries(master)
    .filter(([, i]) => i.status === 'active' && i.url && !/REPLACE_ME/.test(i.url))
    .map(([id, i]) => ({ id, url: i.url }));

  for (const { id, url } of targets) {
    try {
      const ctl = AbortSignal.timeout(10000);
      let res = await fetch(url, { method: 'HEAD', redirect: 'follow', signal: ctl });
      if (res.status === 405 || res.status === 403) {
        res = await fetch(url, { method: 'GET', redirect: 'follow', signal: ctl });
      }
      if (res.status >= 400) {
        errors.push(`${id}: リンク切れの可能性（HTTP ${res.status}） ${url}`);
      }
    } catch (e) {
      warns.push(`${id}: 到達確認に失敗（${e.name}） ${url}`);
    }
  }
  infos.push(`${targets.length} 件のURLに接続確認しました`);
}

/* ---------- 出力 ---------- */

const print = (title, list) => {
  if (!list.length) return;
  console.log(`\n${title}`);
  list.forEach((m) => console.log(`  - ${m}`));
};

console.log(`アフィリエイト点検 ${today}`);
print('要修正', errors);
print('注意', warns);
print('参考', infos);

console.log(
  `\n要修正 ${errors.length} / 注意 ${warns.length}` +
    (DO_FETCH ? '' : '（--fetch でリンク到達性も確認できます）')
);

process.exit(errors.length > 0 ? 1 : 0);
