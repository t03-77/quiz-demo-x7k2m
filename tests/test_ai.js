// AI連携のE2E (APIはモック)
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  // api.anthropic.com をモック
  await ctx.route('https://api.anthropic.com/**', async (route) => {
    const body = JSON.parse(route.request().postData());
    const isConvert = !!body.output_config;
    const text = isConvert
      ? JSON.stringify({ questions: [{ question: 'テスト問題: S3の耐久性は?', n_correct: 1, options: [
          { letter: 'A', text: 'イレブンナイン', correct: true, explanation: '正解です。' },
          { letter: 'B', text: 'ツーナイン', correct: false, explanation: '不正解です。' }] }] })
      : 'モック回答: ゲートウェイ型VPCエンドポイントはネットワーク経路の話です。';
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text }], stop_reason: 'end_turn',
      usage: { input_tokens: 1000, output_tokens: 500 },
    })});
  });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { console.log('dialog:', d.message().slice(0, 50)); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // APIキーを設定
  await page.locator('nav button[data-v="settings"]').click();
  await page.fill('#set-key', 'sk-ant-test-key');
  await page.locator('#set-key').blur();

  // 1問解いてAI質問
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  await page.locator('#ai-presets .chip').first().click(); // もっと簡単に説明して
  await page.waitForFunction(() => document.getElementById('ai-msgs').textContent.includes('モック回答'));
  console.log('AIチャット: 応答表示OK');
  const usage = await page.evaluate(() => document.getElementById('set-usage').textContent);
  console.log('使用額計上:', '$' + usage, '(期待: 1000in+500out Haiku = $0.0035 → 0.00表示)');
  await page.screenshot({ path: '11_ai_chat.png' });
  await page.mouse.click(10, 100); // シートを閉じる

  // AI変換 → 保存
  await page.locator('nav button[data-v="settings"]').click();
  await page.selectOption('#cv-exam', 'SAA-C03');
  await page.fill('#cv-text', 'S3の耐久性について... A. イレブンナイン B. ツーナイン 正解A');
  await page.locator('#cv-run').click();
  await page.waitForSelector('#cv-preview .setrow');
  console.log('変換プレビュー表示OK');
  await page.locator('button:has-text("保存する")').click();
  await page.waitForFunction(() => document.getElementById('cv-count').textContent.includes('1問'));
  console.log('ユーザー問題保存OK');

  // 出題セット「追加」に反映されるか
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  const chips = await page.locator('#h-sets .chip').allInnerTexts();
  console.log('セットチップ:', chips.join(' | '));

  // リロード後もIndexedDBから復元
  await page.reload();
  await page.waitForSelector('.examcard');
  await page.waitForFunction(() => document.getElementById('cv-count') !== null);
  const cnt = await page.evaluate(() => { updateUserCount(); return document.getElementById('cv-count').textContent; });
  console.log('リロード後のユーザー問題:', cnt || '(空)');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
