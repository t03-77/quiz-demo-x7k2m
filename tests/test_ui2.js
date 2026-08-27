// 設定まわりのUI改善を確認する
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

  // 使用モデルの既定値と候補
  await page.locator('nav button[data-v="settings"]').click();
  console.log('既定モデル:', await page.inputValue('#set-model'));
  const opts = await page.locator('#model-presets option').evaluateAll(e => e.map(x => x.value));
  console.log('候補:', opts.join(' / '));
  if (opts[0] !== 'claude-sonnet-5') throw new Error('候補の先頭が最新モデルでない');
  console.log('一覧取得ボタン:', await page.locator('button:has-text("最新のモデル一覧を取得")').count() > 0);

  // 問題ファイルの書き方の例
  const hasSample = await page.locator('details summary:has-text("ファイルの書き方")').count() > 0;
  console.log('JSON例の折りたたみ:', hasSample);
  if (!hasSample) throw new Error('ファイル形式の説明がない');
  await page.locator('details summary:has-text("ファイルの書き方")').click();
  const sample = await page.locator('details pre').innerText();
  console.log('例の中身:', sample.includes('"exam"') && sample.includes('"correct"') ? 'exam/correct を含む' : '不足');

  // 学習データの説明
  const dataNote = await page.locator('.card:has-text("学習データ") .note').first().innerText();
  console.log('学習データの説明:', dataNote.slice(0, 46) + '…');
  if (!/別の端末では引き継がれず/.test(dataNote)) throw new Error('何のための機能か説明されていない');

  // ホーム画面から問題数を変えられるか
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard').first().click();
  await page.waitForSelector('#v-home.on');
  const has = await page.locator('#home-seslen').count() > 0;
  console.log('ホームに問題数の選択:', has, '/ 値:', await page.inputValue('#home-seslen'));
  if (!has) throw new Error('ホームで問題数を変えられない');
  await page.selectOption('#home-seslen', '20');
  await page.locator('nav button[data-v="settings"]').click();
  console.log('設定画面にも反映:', await page.inputValue('#set-seslen'));
  if (await page.inputValue('#set-seslen') !== '20') throw new Error('設定画面と同期していない');

  // 模擬試験の記録についての説明
  const seslenNote = await page.locator('.note', { hasText: '模擬試験モードは' }).first().innerText();
  console.log('模擬試験の記録:', /最後まで解くか時間切れ/.test(seslenNote) ? '正しく説明されている' : '説明なし');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
