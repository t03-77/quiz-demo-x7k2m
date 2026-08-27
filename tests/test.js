// cert_quiz_app スモークE2E: 試験選択 → 試験ホーム → 演習 → 回答まで
const { chromium } = require('playwright-core');
const path = require('path');
const { waitQuestion, answer } = require('./answer');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  // 配布するときだけ置くファイル（音声トラック定義・デモ用キー）は、無くても正常。
  // 404は意図した動作なのでエラーとして数えない
  const OPTIONAL = /audio_tracks|demo_key|\.mp3/;
  page.on('console', m => {
    if (m.type() !== 'error') return;
    if (/ERR_FILE_NOT_FOUND|Failed to load resource/.test(m.text()) && OPTIONAL.test(m.location().url || '')) return;
    errors.push('console: ' + m.text());
  });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);

  // 1. 試験選択画面: 12資格
  await page.waitForSelector('.examcard');
  const nCards = await page.locator('.examcard').count();
  console.log('試験カード数:', nCards, nCards === 12 ? 'OK' : 'NG');
  console.log('バンク状態:', (await page.locator('#bank-status').innerText()).trim());

  // 2. SAAを選ぶ → ホーム
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.waitForSelector('#v-home.on');
  console.log('セットチップ:', (await page.locator('#h-sets .chip').allInnerTexts()).join(' | '));
  console.log('習得表示:', (await page.locator('#h-master').innerText()).replace(/\s+/g, ''));

  // 3. 問題を解く（形式は問わない）
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#v-quiz.on');
  await waitQuestion(page);
  console.log('出題:', await page.evaluate(() => cur.id + ' / ' + (cur.type || 'choice')));

  // 4. 回答して採点
  await answer(page);
  console.log('結果バナー:', (await page.locator('.resultbanner').innerText()).split('\n')[0]);
  console.log('解説ブロック数:', await page.locator('#q-card .expl').count());

  // 5. 次の問題 → 統計
  await page.locator('#q-card .rowbtns button').last().click();
  await page.waitForSelector('#q-card .rowbtns');
  await page.locator('nav button[data-v="stats"]').click();
  await page.waitForSelector('#v-stats.on');
  console.log('統計 正答率:', await page.locator('#s-rate').innerText());

  // 6. AIP-C01 も出題できるか
  await page.locator('#head-exam').click();
  await page.waitForSelector('#v-exams.on');
  await page.locator('.examcard', { hasText: 'Generative AI Developer' }).first().click();
  await page.waitForSelector('#v-home.on');
  console.log('AIPセットチップ:', (await page.locator('#h-sets .chip').allInnerTexts()).join(' | '));
  await page.locator('button:has-text("問題を解く")').click();
  await waitQuestion(page);
  console.log('AIP出題OK');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
