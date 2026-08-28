// ワークスペースIDが必要なAPIキーへの対応を確認する
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  let sentHeaders = null;
  // 実際のAPIと同じく「ワークスペースIDが無い限りエラー」にする
  await ctx.route('https://api.anthropic.com/**', async route => {
    sentHeaders = route.request().headers();
    if (!sentHeaders['anthropic-workspace-id']) {
      await route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({
        error: { message: 'anthropic-workspace-id is required when authenticating with an identity-linked API key; send the id of the workspace this request acts in.' },
      })});
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: 'ワークスペース指定で通りました。' }], stop_reason: 'end_turn',
      usage: { input_tokens: 10, output_tokens: 5 },
    })});
  });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('nav button[data-v="settings"]').click();
  await page.fill('#set-key', 'sk-ant-workspace-test');
  await page.locator('#set-key').blur();

  // ワークスペース未指定でエラーが出たとき、対処方法が日本語で出るか
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard').first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  await page.locator('#ai-presets .chip').first().click();
  await page.waitForFunction(() => /ワークスペース|APIエラー/.test(document.getElementById('ai-msgs').textContent), { timeout: 15000 });
  const msg = await page.locator('#ai-msgs').innerText();
  const jp = /設定の「ワークスペースID」/.test(msg);
  console.log('エラー時の案内:', jp ? '日本語で対処方法が出る' : '★英語のまま');
  if (!jp) throw new Error('対処方法が案内されない');

  // ワークスペースIDを入れるとヘッダーに乗るか
  await page.mouse.click(10, 100);
  await page.locator('nav button[data-v="settings"]').click();
  // ワークスペースID欄は必要になったときだけ出るので、まず「接続を確認」で出させる
  await page.locator('button:has-text("接続を確認")').click();
  await page.waitForSelector('#adv-row', { state: 'visible', timeout: 15000 });
  await page.fill('#set-workspace', 'wrkspc_01TESTWORKSPACE');
  await page.locator('#set-workspace').blur();
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard').first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  await page.locator('#ai-presets .chip').first().click();
  await page.waitForFunction(() => document.getElementById('ai-msgs').textContent.includes('通りました'), { timeout: 15000 });
  console.log('送信ヘッダ anthropic-workspace-id:', sentHeaders['anthropic-workspace-id'] || '(なし)');
  if (sentHeaders['anthropic-workspace-id'] !== 'wrkspc_01testworkspace' &&
      sentHeaders['anthropic-workspace-id'] !== 'wrkspc_01TESTWORKSPACE') {
    throw new Error('ワークスペースIDがヘッダーに乗っていない');
  }

  // 再読み込みしても設定が残るか
  await page.reload();
  await page.waitForSelector('.examcard');
  await page.locator('nav button[data-v="settings"]').click();
  console.log('再読み込み後の設定:', await page.inputValue('#set-workspace'));

  console.log(errors.length ? 'JSエラー ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
