// デモ用キーの解錠を確認する
// 会社などでURLとパスワードだけ渡し、同僚に本物のAIを試してもらう用途
const { chromium } = require('playwright-core');
const path = require('path');

const PASS = 'Test-Passphrase-For-E2E-2026-0827';

/* テスト用のキーをページ内で作って差し込む。
   配布中の本物の demo_key.js に依存すると、パスワードが違って解錠できず
   テストが落ちる（実際にそれで落ちた）。本物のキーには触れない。 */
async function seedKey(page) {
  await page.evaluate(async (pass) => {
    const enc = new TextEncoder();
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const base = await crypto.subtle.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: 1000, hash: 'SHA-256' }, base, 256);
    const k = await crypto.subtle.importKey('raw', bits, 'AES-GCM', false, ['encrypt']);
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, k, enc.encode('sk-ant-test-demo-key-for-e2e'));
    const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
    window.DEMO_KEY = { v: 1, iter: 1000, salt: b64(salt), iv: b64(iv), data: b64(ct) };
    if (window.syncDemoUI) syncDemoUI();
  }, PASS);
}

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
  await seedKey(page);

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

  // 再読み込みしても解錠が続くこと。
  // スマホでアプリを切り替えるとブラウザがページを破棄して再読み込みするため、
  // ここで解けると学習中にAI機能が使えなくなる（実際にその指摘を受けた）
  await page.reload();
  await page.waitForSelector('.examcard');
  const stillUnlocked = await page.evaluate(() => !!UNLOCKED_KEY);
  console.log('再読み込み後も解錠が続く:', stillUnlocked);
  if (!stillUnlocked) throw new Error('再読み込みで解錠が解けてしまう');

  // タブを閉じれば消えること（sessionStorage なので別コンテキストには残らない）
  const other = await browser.newContext({ viewport: { width: 420, height: 900 } });
  const p2 = await other.newPage();
  await p2.goto(url);
  await p2.waitForSelector('.examcard');
  const fresh = await p2.evaluate(() => !UNLOCKED_KEY);
  console.log('別のタブでは解錠されていない:', fresh);
  if (!fresh) throw new Error('別タブにキーが漏れている');
  await other.close();

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
