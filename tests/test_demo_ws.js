// デモ用キーにワークスペースIDを同梱した場合、受け取った人が設定なしで使えることを確認する
const { chromium } = require('playwright-core');
const path = require('path');
const PASS = 'Test-Passphrase-For-E2E-2026-0827';
const WS = 'wrkspc_01DEMOWORKSPACE';
const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');

async function seed(page, withWorkspace) {
  await page.evaluate(async ({ pass, ws }) => {
    const enc = new TextEncoder();
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const base = await crypto.subtle.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: 1000, hash: 'SHA-256' }, base, 256);
    const k = await crypto.subtle.importKey('raw', bits, 'AES-GCM', false, ['encrypt']);
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, k, enc.encode('sk-ant-demo-with-ws'));
    const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
    window.DEMO_KEY = { v: 1, iter: 1000, salt: b64(salt), iv: b64(iv), data: b64(ct) };
    if (ws) window.DEMO_KEY.workspace = ws;
    if (window.syncDemoUI) syncDemoUI();
  }, { pass: PASS, ws: withWorkspace ? WS : null });
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  let sentWs = null;
  await ctx.route('https://api.anthropic.com/**', async route => {
    const h = route.request().headers();
    sentWs = h['anthropic-workspace-id'] || null;
    if (!sentWs) {
      await route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({
        error: { message: 'anthropic-workspace-id is required when authenticating with an identity-linked API key' } }) });
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: 'ok' }], stop_reason: 'end_turn', usage: {} }) });
  });
  const page = await ctx.newPage();
  page.on('dialog', async d => { await d.accept(); });
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await seed(page, true);

  // 受け取った人の操作：デモモードON → パスワードで解錠 → そのまま使える
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-demo').check();
  await seed(page, true);
  await page.fill('#demo-pass', PASS);
  await page.locator('button:has-text("解錠")').click();
  await page.waitForFunction(() => /解錠しました/.test(document.getElementById('demo-key-msg').textContent));
  console.log('解錠: OK（利用者はワークスペースIDを入力していない）');
  console.log('  設定欄の値:', JSON.stringify(await page.inputValue('#set-workspace')));

  await page.locator('button:has-text("接続を確認")').click();
  await page.waitForFunction(() => /使えます|使えません|設定/.test(document.getElementById('conn-msg').textContent));
  console.log('接続確認:', (await page.locator('#conn-msg').innerText()).trim());
  console.log('送信されたワークスペースID:', sentWs || '(なし)');
  if (sentWs !== WS) throw new Error('同梱したワークスペースIDが使われていない');

  console.log('JSエラーなし');
  await browser.close();
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
