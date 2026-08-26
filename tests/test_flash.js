// AIP-C01の「本番形式」と「一問一答」の分離を検証
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push(e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Generative AI Developer' }).first().click();
  await page.waitForSelector('#v-home.on');

  const chips = await page.locator('#h-sets .chip').allInnerTexts();
  console.log('出題セット:', chips.join(' | '));
  console.log('説明文:', await page.locator('#h-setinfo').innerText());

  // 「本番形式」を選ぶと本番形式だけが出るか
  await page.locator('#h-sets .chip', { hasText: '本番形式' }).click();
  console.log('本番形式の説明:', await page.locator('#h-setinfo').innerText());
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#q-card .opt');
  const set1 = await page.evaluate(() => cur.set);
  const qlen = await page.evaluate(() => cur.question.length);
  console.log('出題された問題の種類:', set1, '/ 問題文', qlen, '字');

  // 模擬試験が一問一答を拾わないか
  await page.locator('nav button[data-v="home"]').click();
  await page.waitForSelector('#v-home.on');
  await page.locator('#h-sets .chip', { hasText: 'すべて' }).click();
  await page.locator('.chip:has-text("ウォームアップ")').click();
  await page.waitForSelector('#q-card .opt');
  const mockSets = await page.evaluate(() => MOCK.ids.map(id => byId(id).set));
  const uniq = [...new Set(mockSets)];
  console.log('模試10問の内訳:', uniq.join(','), '/ 一問一答の混入:', mockSets.includes('flash') ? '← あり(NG)' : 'なし(OK)');

  console.log(errors.length ? 'JSエラー: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
