// APIキーなしでAI機能の動きを確認できる「デモモード」のE2E
// 会社などキーを持ち込めない環境で人に見せる用途を想定している
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  // APIに実際に飛んでいないことを確かめるため、通信があれば記録する
  let apiHits = 0;
  await ctx.route('https://api.anthropic.com/**', async route => { apiHits++; await route.abort(); });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { errors.push('想定外のalert: ' + d.message()); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // デモモードをON(APIキーは入れない)
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-demo').check();
  const keyDisabled = await page.locator('#set-key').isDisabled();
  const noteShown = await page.locator('#demo-note').isVisible();
  console.log('APIキー欄が無効化:', keyDisabled, '/ 説明の表示:', noteShown);
  if (!keyDisabled || !noteShown) throw new Error('デモモードのUI切り替えが効いていない');

  // 1問解いてAIに質問
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  const title = await page.locator('#ai-title').innerText();
  console.log('チャットの見出し:', title);
  if (!title.includes('デモ')) throw new Error('デモ表示が出ていない');

  // プリセットを2つ試す。応答が届くたびに「デモ応答」が1つ増えるので、その数で待つ
  let expected = 0;
  for (const label of ['もっと簡単に説明して', 'なぜ他の選択肢は不正解？']) {
    expected++;
    await page.locator('#ai-presets .chip', { hasText: label }).click();
    await page.waitForFunction(
      k => (document.getElementById('ai-msgs').textContent.match(/デモ応答/g) || []).length >= k,
      expected, { timeout: 15000 });
    console.log('「' + label + '」→ 応答あり');
  }
  const reply = await page.locator('#ai-msgs > div').last().innerText();
  console.log('最後の応答(冒頭):', reply.replace(/\n/g, ' ').slice(0, 60));
  await page.screenshot({ path: 'demo_chat.png', fullPage: true });

  // 使用額が増えていないこと(デモは課金されない)
  await page.mouse.click(10, 100);
  await page.locator('nav button[data-v="settings"]').click();
  const usage = await page.locator('#set-usage').innerText();
  console.log('今月の使用額:', '$' + usage, '/ APIへの通信:', apiHits + '回');
  if (parseFloat(usage) !== 0) throw new Error('デモなのに使用額が計上されている');
  if (apiHits !== 0) throw new Error('デモなのにAPIへ通信している');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
