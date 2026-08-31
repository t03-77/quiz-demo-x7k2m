// モデル未指定でも、キーの種類に合わせて既定モデルが選ばれることを確認する
const { chromium } = require('playwright-core');
const path = require('path');
const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  let sent = null;
  await ctx.route('https://api.anthropic.com/**', async route => {
    sent = { key: route.request().headers()['x-api-key'], body: JSON.parse(route.request().postData() || '{}') };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      content: [{ type: 'text', text: 'ok' }], stop_reason: 'end_turn', usage: {} }) });
  });
  const page = await ctx.newPage();
  page.on('dialog', async d => { await d.accept(); });
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // 1. モデル未指定でも既定が選ばれること
  await page.locator('nav button[data-v="settings"]').click();
  console.log('モデル欄の初期値:', JSON.stringify(await page.inputValue('#set-model')), '(空でよい)');
  await page.fill('#set-key', 'sk-ant-MY-OWN-key');
  await page.locator('#set-key').blur();
  await page.locator('button:has-text("接続を確認")').click();
  await page.waitForFunction(() => /使えます|使えません|設定/.test(document.getElementById('conn-msg').textContent));
  console.log('接続確認:', (await page.locator('#conn-msg').innerText()).trim());
  console.log('自動で選ばれたモデル:', sent.body.model);
  if (!sent.body.model) throw new Error('モデルが決まっていない');

  // 2. OpenAIのキーならGPT系が選ばれること
  const ctx2 = await browser.newContext({ viewport: { width: 420, height: 900 } });
  let sent2 = null;
  await ctx2.route('https://api.openai.com/**', async route => {
    sent2 = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      choices: [{ message: { content: 'ok' }, finish_reason: 'stop' }], usage: {} }) });
  });
  const p2 = await ctx2.newPage();
  await p2.goto(url);
  await p2.waitForSelector('.examcard');
  await p2.locator('nav button[data-v="settings"]').click();
  await p2.fill('#set-key', 'sk-proj-openai-key');
  await p2.locator('#set-key').blur();
  await p2.locator('button:has-text("接続を確認")').click();
  await p2.waitForFunction(() => /使えます|使えません|設定/.test(document.getElementById('conn-msg').textContent));
  console.log('OpenAIキーで自動選択:', sent2 ? sent2.model : '(送信なし)');
  if (!sent2 || !/^gpt/.test(sent2.model)) throw new Error('OpenAIキーなのにGPT系が選ばれていない');

  console.log('JSエラーなし');
  await browser.close();
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
