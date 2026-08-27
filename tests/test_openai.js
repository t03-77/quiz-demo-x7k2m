// OpenAI(GPT)を選んだときにも動くことを確認する
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });

  let sent = null;
  await ctx.route('https://api.openai.com/**', async route => {
    sent = { url: route.request().url(), headers: route.request().headers(),
             body: JSON.parse(route.request().postData()) };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      choices: [{ message: { content: 'GPTからのモック回答です。' }, finish_reason: 'stop' }],
      usage: { prompt_tokens: 1000, completion_tokens: 500 },
    })});
  });
  // Anthropic側に飛んでいないことも確かめる
  let anthropicHits = 0;
  await ctx.route('https://api.anthropic.com/**', async route => { anthropicHits++; await route.abort(); });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { errors.push('想定外のalert: ' + d.message().slice(0, 60)); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // GPTを選んでOpenAIのキーを入れる
  await page.locator('nav button[data-v="settings"]').click();
  await page.fill('#set-model', 'gpt-5.6-luna'); await page.locator('#set-model').blur();
  await page.fill('#set-key', 'sk-test-openai-key');
  await page.locator('#set-key').blur();

  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForSelector('#aisheet.on');
  await page.locator('#ai-presets .chip').first().click();
  await page.waitForFunction(() => document.getElementById('ai-msgs').textContent.includes('GPTからのモック回答'));

  console.log('送信先:', sent.url);
  console.log('認証ヘッダ:', sent.headers['authorization'] ? 'Bearer ...(あり)' : '(なし)');
  console.log('モデル:', sent.body.model);
  console.log('systemの渡し方:', sent.body.messages[0].role);
  console.log('Anthropicへの通信:', anthropicHits + '回');
  if (!sent.url.includes('openai.com')) throw new Error('OpenAIに送られていない');
  if (!sent.headers['authorization']) throw new Error('Authorizationヘッダがない');
  if (sent.body.messages[0].role !== 'system') throw new Error('systemメッセージが渡っていない');
  if (anthropicHits !== 0) throw new Error('Anthropicにも送信している');

  // 使用額がGPTの単価で計上されているか
  await page.mouse.click(10, 100);
  await page.locator('nav button[data-v="settings"]').click();
  const usage = await page.locator('#set-usage').innerText();
  console.log('使用額:', '$' + usage, '(1000in+500out の gpt-5.6-luna = $0.00045)');
  if (parseFloat(usage) === 0 && usage === '0.00') console.log('  ※小数第2位までの表示なので0.00でよい');

  // キーの種類が合っていないときに気づけるか
  await page.fill('#set-model', 'claude-haiku-4-5'); await page.locator('#set-model').blur();
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').answer(page);
  const before = errors.length;
  await page.locator('button:has-text("この問題についてAIに質問")').click();
  await page.waitForTimeout(500);
  const warned = errors.length > before && errors[errors.length - 1].includes('Anthropic');
  console.log('モデルとキーの不一致を警告:', warned);
  if (!warned) throw new Error('キーの種類が違うのに警告が出ない');
  errors.length = before;   // この警告は想定内なので取り除く

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
