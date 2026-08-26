// 公式バンク読み込み(IndexedDB)のE2E
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { console.log('dialog:', d.message().slice(0, 60)); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // questions_all.json を読み込む
  await page.setInputFiles('#bankfile', 'C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/資料/変換済み/questions_all.json');
  await page.waitForFunction(() => document.getElementById('bank-status').textContent.includes('読み込み済み'), null, { timeout: 20000 });
  console.log('バンク状態:', (await page.locator('#bank-status').innerText()).trim());

  // SCS-C03(needs_review 3問除外 → 公式82問)を確認
  await page.locator('.examcard', { hasText: 'Security – Specialty' }).first().click();
  await page.waitForSelector('#v-home.on');
  console.log('SCSセットチップ:', (await page.locator('#h-sets .chip').allInnerTexts()).join(' | '));

  // Pretestに絞ってマッチング/並び替えが出るか(順番どおりで47問目以降は欠損スキップ確認は省略)
  await page.locator('#h-sets .chip', { hasText: 'Pretest' }).click();
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#v-quiz.on');
  await page.waitForSelector('#q-card .rowbtns');
  console.log('Pretest出題ID:', await page.locator('#q-card .tag').first().innerText());
  await page.screenshot({ path: '7_official.png', fullPage: true });

  // リロード後もIndexedDBから復元されるか
  await page.reload();
  await page.waitForSelector('.examcard');
  await page.waitForFunction(() => document.getElementById('bank-status').textContent.includes('読み込み済み'), null, { timeout: 10000 });
  console.log('リロード後:', (await page.locator('#bank-status').innerText()).trim());

  console.log(errors.length ? 'JSエラー ' + errors.length + '件:' : 'JSエラーなし');
  errors.forEach(e => console.log(' ', e));
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
