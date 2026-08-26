// 模擬試験モードのE2E
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
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.waitForSelector('#v-home.on');

  // 模試10問を開始
  await page.locator('.chip', { hasText: '10問 / 20分' }).click();
  await page.waitForSelector('#v-quiz.on');
  await require('./answer').waitQuestion(page);
  console.log('模試ヘッダ:', await page.locator('#q-card .tag').first().innerText());
  const timeTxt = await page.locator('#mock-time').innerText().catch(() => '');
  console.log('タイマー表示:', timeTxt || '(初回tick待ち)');
  await page.screenshot({ path: '8_mock_q.png' });

  // 10問すべて先頭の選択肢で回答
  const { choose } = require('./answer');
  for (let i = 0; i < 10; i++) await choose(page);   // 模試は途中で採点画面を出さない
  await page.waitForSelector('.resultbanner');
  console.log('結果:', (await page.locator('.resultbanner').innerText()).replace(/\n/g, ' '));
  const nRows = await page.locator('#q-card .weakitem').count();
  console.log('結果一覧行数:', nRows);
  await page.screenshot({ path: '9_mock_result.png', fullPage: true });

  // 1問目のレビュー → 戻る → 終了
  await page.locator('#q-card .weakitem').first().click();
  await page.waitForSelector('.expl');
  console.log('レビュー表示OK');
  await page.locator('button:has-text("結果一覧へ戻る")').click();
  await page.waitForSelector('#q-card .weakitem');
  await page.locator('button:has-text("終了する")').click();
  await page.waitForSelector('#v-home.on');
  console.log('ホーム復帰OK, 延べ回答:', await page.locator('#h-count').innerText());

  console.log(errors.length ? 'JSエラー ' + errors.length + '件:' : 'JSエラーなし');
  errors.forEach(e => console.log(' ', e));
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
