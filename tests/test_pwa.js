// PWA(オフライン対応)のE2E: HTTPで配信し、SW登録 → オフライン化 → 再読込で起動するか
const { chromium } = require('playwright-core');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = 'C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app';
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg' };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/index.html';
  const f = path.join(ROOT, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nf'); }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(8731, r));
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8731/index.html');
  await page.waitForSelector('.examcard');

  // Service Worker の登録を待つ
  const reg = await page.evaluate(async () => {
    const r = await navigator.serviceWorker.ready.catch(() => null);
    return r ? r.active?.state : null;
  });
  console.log('Service Worker:', reg || '← 未登録');

  // manifest が読めるか
  const mf = await page.evaluate(async () => {
    const r = await fetch('manifest.webmanifest');
    return r.ok ? (await r.json()).name : null;
  });
  console.log('マニフェスト:', mf || '← 読めない');

  // キャッシュに入ったか
  const cached = await page.evaluate(async () => {
    const ks = await caches.keys();
    if (!ks.length) return 0;
    return (await (await caches.open(ks[0])).keys()).length;
  });
  console.log('キャッシュ済みファイル数:', cached);

  // オフラインにして再読込 → 起動するか
  await ctx.setOffline(true);
  await page.reload();
  await page.waitForSelector('.examcard', { timeout: 15000 });
  const n = await page.locator('.examcard').count();
  console.log('オフラインで再読込 → 試験カード', n, '件表示');

  // オフラインでも問題が解けるか
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  console.log('オフラインで採点まで:', (await page.locator('.resultbanner').innerText()).split('\n')[0]);
  await page.waitForTimeout(3500);   // 状態の定期チェックを待つ
  const bar = await page.locator('#offbar').isVisible().catch(() => false);
  console.log('オフライン通知バー:', bar ? '表示' : '← 非表示');

  console.log(errors.length ? 'JSエラー: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  server.close();
})();
