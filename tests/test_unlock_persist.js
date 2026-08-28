// 解錠したあと、再読み込みしても使い続けられることを確認する
// （スマホでアプリを切り替えるとブラウザがページを破棄して再読み込みするため）
const { chromium } = require('playwright-core');
const path = require('path');
const PASS = 'Test-Passphrase-For-E2E-2026-0827';

async function seedKey(page) {
  await page.evaluate(async (pass) => {
    const enc = new TextEncoder();
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const base = await crypto.subtle.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: 1000, hash: 'SHA-256' }, base, 256);
    const k = await crypto.subtle.importKey('raw', bits, 'AES-GCM', false, ['encrypt']);
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, k, enc.encode('sk-ant-persist-test-key'));
    const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
    window.DEMO_KEY = { v: 1, iter: 1000, salt: b64(salt), iv: b64(iv), data: b64(ct) };
    if (window.syncDemoUI) syncDemoUI();
  }, PASS);
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  let sentKey = null;
  await ctx.route('https://api.anthropic.com/**', async route => {
    sentKey = route.request().headers()['x-api-key'];
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: '本物のAIからの応答です。' }], stop_reason: 'end_turn',
      usage: { input_tokens: 10, output_tokens: 5 },
    })});
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('dialog', async d => { errors.push('alert: ' + d.message().slice(0, 40)); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await seedKey(page);

  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-demo').check();
  await seedKey(page);
  await page.fill('#demo-pass', PASS);
  await page.locator('button:has-text("解錠")').click();
  await page.waitForFunction(() => /解錠しました/.test(document.getElementById('demo-key-msg').textContent));
  console.log('解錠:', await page.evaluate(() => !!UNLOCKED_KEY));

  // 再読み込み（スマホでアプリを切り替えたときに起きること）
  await page.reload();
  await page.waitForSelector('.examcard');
  await seedKey(page);
  const kept = await page.evaluate(() => !!UNLOCKED_KEY);
  console.log('再読み込み後も解錠が続く:', kept);
  if (!kept) throw new Error('再読み込みで解錠が解けてしまう');

  // 用語説明からAIを呼べるか
  await page.locator('.examcard').first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#q-card .opt, #q-card select');
  if (await page.locator('#q-card .term').count()) {
    await page.locator('#q-card .term').first().click();
    await page.waitForSelector('#sheet.on');
    await page.locator('button:has-text("この用語についてAIに聞く")').click();
    await page.waitForSelector('#aisheet.on');
    await page.locator('#ai-presets .chip').first().click();
    await page.waitForFunction(() => document.getElementById('ai-msgs').textContent.includes('本物のAI'), { timeout: 15000 });
    console.log('用語説明からAIを呼べた / 送られたキー:', sentKey ? sentKey.slice(0, 14) + '...' : '(なし)');
    if (!sentKey) throw new Error('用語説明からAPIが呼ばれていない');
  }

  // 解除できるか（開いているチャットを閉じてから）
  await page.evaluate(() => document.querySelectorAll('.sheet.on').forEach(s => s.classList.remove('on')));
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('button:has-text("解除する")').click();
  await page.waitForFunction(() => /解除しました/.test(document.getElementById('demo-key-msg').textContent));
  console.log('解除後:', await page.evaluate(() => !UNLOCKED_KEY && demoMode()) ? 'デモ応答に戻る' : '★戻らない');

  // 端末に残っていないこと
  const stored = await page.evaluate(() => ({
    local: JSON.stringify(localStorage).includes('sk-ant-persist'),
    session: sessionStorage.getItem('certquiz_demo_unlocked'),
  }));
  console.log('localStorageへの保存:', stored.local ? '★あり' : 'なし');
  console.log('sessionStorage:', stored.session ? '★残っている' : '解除で消えた');
  if (stored.local) throw new Error('キーが端末に永続保存されている');

  console.log(errors.length ? 'JSエラー ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
