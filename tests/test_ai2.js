// AI機能の未検証パス: 画像入力 / 予算上限の自動停止 / エラー処理
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

// 1x1 PNG
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
fs.writeFileSync('shot.png', PNG);

(async () => {
  const errors = [], dialogs = [];
  let sentBody = null;
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  await ctx.route('https://api.anthropic.com/**', async (route) => {
    sentBody = JSON.parse(route.request().postData());
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: JSON.stringify({ questions: [{ question: '画像から抽出した問題', n_correct: 1,
        options: [{letter:'A',text:'正',correct:true,explanation:'正解です。'},{letter:'B',text:'誤',correct:false,explanation:'不正解です。'}] }] }) }],
      stop_reason: 'end_turn', usage: { input_tokens: 2000000, output_tokens: 1000000 },  // 高額にして予算超過を誘発
    })});
  });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push(e.message));
  page.on('dialog', async d => { dialogs.push(d.message()); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('nav button[data-v="settings"]').click();
  await page.fill('#set-key', 'sk-ant-test');
  await page.locator('#set-key').blur();

  // --- 画像から変換 ---
  await page.setInputFiles('#cv-imgs', path.resolve('shot.png'));
  await page.locator('#cv-run').click();
  await page.waitForSelector('#cv-preview .setrow', { timeout: 15000 });
  const hasImage = sentBody.messages[0].content.some(b => b.type === 'image');
  const mediaType = sentBody.messages[0].content.find(b => b.type === 'image')?.source?.media_type;
  console.log('画像ブロック送信:', hasImage, '/ media_type:', mediaType);
  console.log('スキーマ指定:', !!sentBody.output_config, '/ モデル:', sentBody.model);
  console.log('プレビュー表示:', (await page.locator('#cv-preview .setrow').first().innerText()).slice(0, 30));

  // --- 予算上限の自動停止 (Haiku: 2M in + 1M out = $2+$5 = $7 > $2上限) ---
  const usage = await page.locator('#set-usage').innerText();
  console.log('計上された使用額: $' + usage, '(上限$2を超過)');
  dialogs.length = 0;
  await page.locator('#cv-run').click();
  await page.waitForTimeout(600);
  const blocked = dialogs.some(d => d.includes('予算上限'));
  console.log('予算超過でAI停止:', blocked, blocked ? '' : '← 実装漏れ');

  // --- APIエラー時の扱い ---
  await ctx.route('https://api.anthropic.com/**', r => r.fulfill({ status: 401, contentType: 'application/json',
    body: JSON.stringify({ error: { message: 'invalid x-api-key' } }) }));
  await page.evaluate(() => { SETTINGS.budget = 999; lsSet(SETTINGS_KEY, SETTINGS); });
  dialogs.length = 0;
  await page.locator('#cv-run').click();
  await page.waitForTimeout(800);
  console.log('APIエラーの通知:', dialogs.find(d => d.includes('失敗')) ? 'OK: ' + dialogs[0].slice(0, 50) : '← 通知なし');
  const btnBack = await page.locator('#cv-run').innerText();
  console.log('エラー後にボタン復帰:', btnBack.includes('変換'));

  console.log(errors.length ? 'JSエラー: ' + errors[0] : 'JSエラーなし');
  await browser.close();
})();
