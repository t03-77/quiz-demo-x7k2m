// 解説画面の図解(Mermaid)のE2E
// 図はCDNから読み込むため、読み込めない環境では枠ごと消えることも確かめる
const { chromium } = require('playwright-core');
const path = require('path');

const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');

async function openWithDiagram(page) {
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#q-card .opt, #q-card select');
  // 図が引き当たる問題を探して開く
  const info = await page.evaluate(() => {
    const q = examQuestions(currentExam).find(x => findDiagram(x));
    if (!q) return null;
    startSingleReview(q.id);
    return { id: q.id, title: findDiagram(q).title };
  });
  if (!info) throw new Error('図が引き当たる問題が1問もない');
  await page.waitForSelector('#q-card .opt');
  const i = await page.evaluate(() => displayOpts(cur).findIndex(o => o.correct));
  await page.locator('#q-card .opt').nth(Math.max(0, i)).click();
  await page.locator('#q-card button:has-text("回答する")').click();
  await page.waitForSelector('.resultbanner');
  return info;
}

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  // --- 図が表示される ---
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });
  const info = await openWithDiagram(page);
  console.log('図が付く問題:', info.id, '/', info.title);
  await page.waitForSelector('#diagram-body svg', { timeout: 30000 });
  const box = await page.locator('#diagram-body svg').boundingBox();
  const win = await page.evaluate(() => window.innerWidth);
  console.log('図の幅:', Math.round(box.width), '/ 画面幅:', win);
  if (box.width > win) throw new Error('図が画面からはみ出している');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  if (overflow) throw new Error('横スクロールが発生している');
  await page.screenshot({ path: 'diagram.png', fullPage: true });

  // タップで拡大できる(狭い画面では縮小されて読めないため)
  await page.locator('#diagram-body svg').click();
  await page.waitForSelector('.zoomwrap svg');
  const big = await page.locator('.zoomwrap svg').boundingBox();
  console.log('拡大後の図の幅:', Math.round(big.width), '(拡大前', Math.round(box.width) + ')');
  if (big.width <= box.width) throw new Error('拡大されていない');
  await page.screenshot({ path: 'diagram_zoom.png' });
  await page.locator('.zoomwrap').click({ position: { x: 5, y: 5 } });
  await page.waitForFunction(() => !document.querySelector('.zoomwrap'));
  console.log('タップで閉じる OK');

  // 図のカバー範囲も見ておく
  const cover = await page.evaluate(() => {
    const all = ORIG.filter(q => q.set === 'orig');
    const hit = all.filter(q => findDiagram(q));
    const per = {};
    hit.forEach(q => { per[q.exam] = (per[q.exam] || 0) + 1; });
    return { total: all.length, hit: hit.length, per };
  });
  console.log('図が付く問題数:', cover.hit + '/' + cover.total,
    '(' + Math.round(100 * cover.hit / cover.total) + '%)');
  console.log('  資格別:', JSON.stringify(cover.per));

  // --- CDNが使えないときは図の枠ごと消える ---
  const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx2.route('https://cdn.jsdelivr.net/**', r => r.abort());
  const page2 = await ctx2.newPage();
  page2.on('pageerror', e => errors.push('pageerror(offline): ' + e.message));
  page2.on('dialog', async d => { await d.accept(); });
  await openWithDiagram(page2);
  await page2.waitForFunction(() => !document.getElementById('diagram-box'), { timeout: 20000 });
  console.log('CDNが使えないとき: 図の枠を消して解説だけ表示 OK');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
