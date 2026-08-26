// 新機能追加後のレイアウト目視確認
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
  await page.screenshot({ path: 'v1_exams.png' });

  await page.locator('.examcard', { hasText: 'Cloud Practitioner' }).first().click();
  await page.waitForSelector('#v-home.on');
  await page.screenshot({ path: 'v2_home.png' });

  await page.locator('nav button[data-v="settings"]').click();
  await page.screenshot({ path: 'v3_settings.png', fullPage: true });

  console.log('資格カードの問題数:', (await page.locator('.examcard').first().innerText()).replace(/\n/g, ' '));
  console.log(errors.length ? 'JSエラー: ' + errors[0] : 'JSエラーなし');
  await browser.close();
})();
