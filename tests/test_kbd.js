// キーボード操作のE2E
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 900, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').startChoiceQuestion(page);   // キー操作は選択式のみ対象

  // B キーで2番目の選択肢を選択
  await page.keyboard.press('b');
  const selIdx = await page.locator('#q-card .opt').evaluateAll(els => els.findIndex(e => e.classList.contains('sel')));
  console.log('Bキー → 選択された位置:', selIdx, '(期待1)');

  // Enter で回答
  await page.keyboard.press('Enter');
  await page.waitForSelector('.resultbanner');
  console.log('Enter → 採点画面:', (await page.locator('.resultbanner').innerText()).split('\n')[0]);

  // Enter で次の問題
  await page.keyboard.press('Enter');
  await require('./answer').waitQuestion(page);
  console.log('Enter → 次の問題へ遷移OK');

  // 入力欄フォーカス中は無効であること
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-key').focus();
  await page.keyboard.press('a');
  const val = await page.locator('#set-key').inputValue();
  console.log('入力欄では文字入力として動作:', val === 'a');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
