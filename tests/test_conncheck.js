// APIキーの疎通確認。利用者が細かい仕様を知らなくても、次に何をすればよいか分かること
const { chromium } = require('playwright-core');
const path = require('path');

const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');

async function open(browser, handler) {
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  await ctx.route('https://api.anthropic.com/**', handler);
  const page = await ctx.newPage();
  page.on('dialog', async d => { await d.accept(); });
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('nav button[data-v="settings"]').click();
  await page.fill('#set-key', 'sk-ant-conn-check');
  await page.locator('#set-key').blur();
  return { ctx, page };
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  // 1. 正常に使える場合
  {
    const { ctx, page } = await open(browser, r => r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ content: [{ type: 'text', text: 'ok' }], stop_reason: 'end_turn', usage: {} }),
    }));
    await page.locator('button:has-text("接続を確認")').click();
    await page.waitForFunction(() => !/確認しています/.test(document.getElementById('conn-msg').textContent));
    console.log('正常時:', (await page.locator('#conn-msg').innerText()).trim());
    console.log('  詳細設定の表示:', await page.locator('#adv-row').isVisible() ? '★出ている' : '隠れている（正しい）');
    await ctx.close();
  }

  // 2. ワークスペースIDが要る場合
  {
    const { ctx, page } = await open(browser, r => r.fulfill({
      status: 400, contentType: 'application/json',
      body: JSON.stringify({ error: { message: 'anthropic-workspace-id is required when authenticating with an identity-linked API key' } }),
    }));
    await page.locator('button:has-text("接続を確認")').click();
    await page.waitForFunction(() => !/確認しています/.test(document.getElementById('conn-msg').textContent));
    console.log('ワークスペースIDが必要:', (await page.locator('#conn-msg').innerText()).trim());
    const shown = await page.locator('#adv-row').isVisible();
    console.log('  入力欄が自動で出る:', shown);
    if (!shown) throw new Error('必要な設定欄が出てこない');
    await ctx.close();
  }

  // 3. キーが誤っている場合
  {
    const { ctx, page } = await open(browser, r => r.fulfill({
      status: 401, contentType: 'application/json',
      body: JSON.stringify({ error: { message: 'invalid x-api-key' } }),
    }));
    await page.locator('button:has-text("接続を確認")').click();
    await page.waitForFunction(() => !/確認しています/.test(document.getElementById('conn-msg').textContent));
    console.log('キーが誤り:', (await page.locator('#conn-msg').innerText()).trim());
    await ctx.close();
  }

  // 4. モデル名が誤っている場合
  {
    const { ctx, page } = await open(browser, r => r.fulfill({
      status: 404, contentType: 'application/json',
      body: JSON.stringify({ error: { message: 'model: claude-x does not exist' } }),
    }));
    await page.locator('button:has-text("接続を確認")').click();
    await page.waitForFunction(() => !/確認しています/.test(document.getElementById('conn-msg').textContent));
    console.log('モデル名が誤り:', (await page.locator('#conn-msg').innerText()).trim());
    await ctx.close();
  }

  console.log('JSエラーなし');
  await browser.close();
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
