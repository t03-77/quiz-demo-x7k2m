// 1セットの問題数を設定で変えられること、途中でやめても記録が残ることを確認
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } });
  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // 説明文にテンプレートの書き損じが残っていないか
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  await page.waitForSelector('#v-home.on');
  const note = await page.locator('#v-home .note', { hasText: '1セットは' }).first().innerText();
  if (/\$\{/.test(note)) throw new Error('説明文にテンプレートの記号が残っている: ' + note.slice(0, 60));
  console.log('セット数の表示:', (note.match(/1セットは\s*(\d+)\s*問/) || [])[0] || '(見つからない)');

  // 設定で5問に変更
  await page.locator('nav button[data-v="settings"]').click();
  await page.selectOption('#set-seslen', '5');
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  const note2 = await page.locator('#v-home .note', { hasText: '1セットは' }).first().innerText();
  console.log('変更後の表示:', (note2.match(/1セットは\s*(\d+)\s*問/) || [])[0]);
  if (!/1セットは\s*5\s*問/.test(note2)) throw new Error('設定が説明文に反映されていない');

  // 5問解いたらセットが終わるか
  await page.locator('button:has-text("問題を解く")').click();
  const { answer } = require('./answer');
  for (let i = 0; i < 5; i++) {
    const head = await page.locator('#q-card .tag').first().innerText();
    if (i === 0) console.log('1問目のヘッダ:', head);
    await answer(page);
    if (i < 4) await page.locator('#q-card .rowbtns button').last().click();
  }
  const last = await page.locator('#q-card .rowbtns button').last().innerText();
  console.log('5問目のあとのボタン:', last);
  if (!last.includes('結果')) throw new Error('5問でセットが終わっていない');

  // 途中でやめても記録が残るか(3問だけ解いてリロード)
  await page.evaluate(() => { P = {questions:{}, history:[]}; saveP(); });
  await page.reload();
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  for (let i = 0; i < 3; i++) {
    await answer(page);
    if (i < 2) await page.locator('#q-card .rowbtns button').last().click();
  }
  await page.reload();   // セットの途中で離脱
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  const cnt = await page.locator('#h-count').innerText();
  console.log('3問解いて離脱→再訪したときの延べ回答:', cnt);
  if (parseInt(cnt) !== 3) throw new Error('途中離脱で記録が失われている (期待3, 実際' + cnt + ')');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
