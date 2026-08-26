// 音声ページ(実音声+チャプター)のE2E
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('nav button[data-v="audio"]').click();
  await page.waitForSelector('.audiotrack');
  const n = await page.locator('.audiotrack').count();
  console.log('トラック数:', n);
  console.log('注記:', (await page.locator('#audio-note').innerText()).slice(0, 40) + '…');

  // 1トラック目を再生 → チャプター表示 → チャプターでシーク
  await page.locator('.audiotrack').first().click();
  await page.waitForSelector('#tracklist .chip');
  const nCh = await page.locator('#tracklist .chip').count();
  console.log('表示チャプター数:', nCh);
  await page.locator('#tracklist .chip').nth(1).click(); // Q1-002 (231.8s)
  await page.waitForTimeout(800);
  const cur = await page.evaluate(() => document.getElementById('player').currentTime);
  const playing = await page.evaluate(() => !document.getElementById('player').paused);
  console.log('シーク位置:', Math.round(cur), '秒 / 再生中:', playing);
  await page.screenshot({ path: '10_audio.png', fullPage: false });

  console.log(errors.length ? 'JSエラー ' + errors.length + '件' : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
