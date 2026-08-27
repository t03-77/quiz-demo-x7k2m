// おまかせ出題で「一問一答」ばかり出ないことを確認する
// AIP-C01は一問一答221問 > 本番形式106問なので、素直に混ぜると7割が短い問題になってしまう
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'AIP' }).first().click();
  await page.waitForSelector('#v-home.on');

  // おまかせ出題の対象がどう構成されているか
  const r = await page.evaluate(() => {
    setFilter = 'all';
    const p = pool();
    const per = {};
    p.forEach(q => { per[q.set || '?'] = (per[q.set || '?'] || 0) + 1; });
    return { total: p.length, per, exam: currentExam };
  });
  console.log('おまかせ出題の対象:', r.exam, r.total + '問', JSON.stringify(r.per));
  if (r.per.flash) throw new Error('おまかせ出題に一問一答が混ざっている');

  // 一問一答を明示的に選べば出ること(機能自体は残す)
  const f = await page.evaluate(() => {
    setFilter = 'flash';
    const p = pool();
    setFilter = 'all';
    return p.length;
  });
  console.log('一問一答を選んだとき:', f + '問（選べば使える）');
  if (f < 100) throw new Error('一問一答が選べなくなっている');

  // 実際に出題して、短すぎる問題が出ないか
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#q-card .opt, #q-card select');
  const lens = [];
  for (let i = 0; i < 5; i++) {
    const info = await page.evaluate(() => ({ id: cur.id, set: cur.set, len: cur.question.length }));
    lens.push(info);
    await require('./answer').answer(page);
    const next = page.locator('#q-card .rowbtns button').last();
    if (await next.count()) await next.click();
    await page.waitForSelector('#q-card .opt, #q-card select', { timeout: 15000 }).catch(() => {});
  }
  console.log('出題された5問:');
  lens.forEach(x => console.log('  ', x.id, x.set, x.len + '字'));
  const short = lens.filter(x => x.len < 100);
  if (short.length) throw new Error('100字未満の問題が出題された: ' + short.map(x => x.id).join(','));

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
