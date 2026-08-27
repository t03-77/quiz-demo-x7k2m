// 不具合報告の機能を確認する
// 使う人が問題文を書き写さずに「この問題おかしい」と知らせられること
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 420, height: 900 },
    permissions: ['clipboard-read', 'clipboard-write'],
  });

  let posted = null;
  await ctx.route('https://formspree.io/**', async route => {
    posted = JSON.parse(route.request().postData());
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
  });

  const page = await ctx.newPage();
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  // 選択肢のある問題で確かめる（マッチングや並び替えだと options が無い）
  await require('./answer').startChoiceQuestion(page);
  await require('./answer').answer(page);

  // 送信先が未設定のときは「コピー」だけ出る
  await page.locator('button:has-text("この問題を報告する")').click();
  await page.waitForSelector('#repsheet.on');
  let btns = await page.locator('#rep-actions button').allInnerTexts();
  console.log('送信先が未設定のとき:', btns.join(' / '));
  if (btns.some(b => b.includes('送信'))) throw new Error('送信先が無いのに送信ボタンが出ている');

  // 送る内容に問題の情報が入っているか(報告者が書き写さなくてよいこと)
  await page.selectOption('#rep-kind', { index: 0 });
  await page.fill('#rep-note', 'Bも正解になると思います');
  // details が閉じていると innerText は空になるので textContent で取る
  const preview = await page.locator('#rep-preview').textContent();
  const qid = await page.evaluate(() => cur.id);
  const checks = {
    '問題ID': preview.includes(qid),
    '問題文': preview.includes(await page.evaluate(() => cur.question.slice(0, 20))),
    '選択肢と正解': /\[正解\]/.test(preview),
    '報告者の記入': preview.includes('Bも正解になると思います'),
    '回答状況': /この人の回答/.test(preview),
    '環境': /環境:/.test(preview),
  };
  Object.entries(checks).forEach(([k, v]) => console.log('  ' + k + ':', v ? '含まれる' : '★含まれない'));
  if (Object.values(checks).some(v => !v)) throw new Error('報告に必要な情報が欠けている');

  // コピーできるか
  await page.locator('#rep-actions button:has-text("コピー")').click();
  await page.waitForFunction(() => /コピーしました/.test(document.getElementById('rep-msg').textContent));
  const clip = await page.evaluate(() => navigator.clipboard.readText());
  console.log('クリップボードの中身:', clip.length + '字', clip.includes(qid) ? '(問題IDあり)' : '(問題IDなし)');

  // 送信先を設定すると送信ボタンが出て、実際にPOSTされるか
  await page.evaluate(() => { window.REPORT_ENDPOINT = 'https://formspree.io/f/testtest'; });
  await page.locator('#repsheet .iconbtn').click();
  await page.locator('button:has-text("この問題を報告する")').click();
  btns = await page.locator('#rep-actions button').allInnerTexts();
  console.log('送信先を設定したとき:', btns.join(' / '));
  await page.fill('#rep-note', '正解がおかしいです');
  await page.locator('#rep-actions button:has-text("送信する")').click();
  await page.waitForFunction(() => /送信しました/.test(document.getElementById('rep-msg').textContent), { timeout: 15000 });
  console.log('送信の件名:', posted.subject);
  console.log('本文に問題ID:', posted.message.includes(qid));
  if (!posted.message.includes(qid)) throw new Error('送信内容に問題IDがない');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
