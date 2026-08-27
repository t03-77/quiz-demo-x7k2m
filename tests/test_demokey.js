// デモ用キーの解錠を確認する
// 会社などでURLとパスワードだけ渡し、同僚に本物のAIを試してもらう用途
const { chromium } = require('playwright-core');
const path = require('path');

const PASS = 'Test-Passphrase-For-E2E-2026-0827';

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  let sentKey = null;
  await ctx.route('https://api.anthropic.com/**', async route => {
    sentKey = route.request().headers()['x-api-key'];
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: '本物のAIからの応答です。' }], stop_reason: 'end_turn',
      usage: { input_tokens: 100, output_tokens: 50 },
    })});
  });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { errors.push('想定外のalert: ' + d.message().slice(0, 50)); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // デモモードをONにすると解錠の入口が出る
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-demo').check();
  const rowVisible = await page.locator('#demo-key-row').isVisible();
  console.log('解錠の入口が出る:', rowVisible);
  if (!rowVisible) throw new Error('デモ用キーがあるのに入口が出ない');

  // 間違ったパスワードでは解錠できない
  await page.fill('#demo-pass', 'wrong-password-xxxxxxxxxxxx');
  await page.locator('button:has-text("解錠して本物のAIを試す")').click();
  await page.waitForFunction(() => /違う/.test(document.getElementById('demo-key-msg').textContent), { timeout: 30000 });
  console.log('間違ったパスワード:', (await page.locator('#demo-key-msg').innerText()).trim());
  const stillDemo = await page.evaluate(() => demoMode());
  if (!stillDemo) throw new Error('解錠に失敗したのにデモモードが解除された');

  // 正しいパスワードで解錠
  await page.fill('#demo-pass', PASS);
  await page.locator('button:has-text("解錠して本物のAIを試す")').click();
  await page.waitForFunction(() => /解錠しました/.test(document.getElementById('demo-key-msg').textContent), { timeout: 30000 });
  console.log('正しいパスワード: 解錠OK');
  const cleared = await page.inputValue('#demo-pass');
  console.log('入力欄がクリアされたか:', cleared === '');

  // 実際にAPIへ送られるか(デモ応答ではなく本物の経路)
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  await page.locator('#ai-presets .chip').first().click();
  await page.waitForFunction(() => document.getElementById('ai-msgs').textContent.includes('本物のAI'));
  console.log('APIに送られたキー:', sentKey ? sentKey.slice(0, 12) + '...' : '(なし)');
  if (!sentKey || !sentKey.startsWith('sk-ant-test-demo')) throw new Error('復号したキーがAPIに渡っていない');

  // 端末に保存されていないこと(ここが重要)
  const saved = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('certquiz_settings') || '{}');
    return { key: s.key || '', hasUnlocked: JSON.stringify(s).includes('sk-ant-test-demo') };
  });
  console.log('localStorage内のキー:', saved.key === '' ? '(空)' : '★保存されている');
  if (saved.hasUnlocked) throw new Error('復号したキーが端末に保存されてしまっている');

  // 再読み込みすると解錠が解ける
  await page.reload();
  await page.waitForSelector('.examcard');
  const afterReload = await page.evaluate(() => demoMode());
  console.log('再読み込み後にデモモードへ戻る:', afterReload);
  if (!afterReload) throw new Error('リロードしてもキーが残っている');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
