// 複数選択(2つ選べ・3つ選べ)の入力制約を確認する
// 足りないまま提出できたり、指定数を超えて選べたりすると本番の練習にならない
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'DevOps Engineer' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await page.waitForSelector('#q-card .opt, #q-card select');

  for (const need of [3, 2]) {
    const info = await page.evaluate(n => {
      const q = examQuestions(currentExam).find(x => (x.n_correct || 1) === n && (x.type || 'choice') === 'choice');
      if (!q) return null;
      startSingleReview(q.id);
      return { id: q.id, need: q.n_correct, opts: q.options.length };
    }, need);
    if (!info) { console.log(need + 'つ選択の問題が見つからない'); continue; }
    await page.waitForSelector('#q-card .opt');
    console.log('---', info.id, '(' + info.need + '正解 /' + info.opts + '肢) ---');

    // 1つだけ選んだ状態では回答できないこと
    await page.locator('#q-card .opt').nth(0).click();
    let btn = await page.locator('#q-card .rowbtns button').last();
    console.log('1つ選択時のボタン:', (await btn.innerText()).trim(), '/ 押せるか:', await btn.isEnabled());
    if (await btn.isEnabled()) throw new Error('足りないまま回答できてしまう');

    // 指定数を超えて選べないこと
    for (let i = 1; i < info.opts; i++) await page.locator('#q-card .opt').nth(i).click();
    const selected = await page.locator('#q-card .opt.sel').count();
    console.log('全部タップした後の選択数:', selected, '(上限' + info.need + ')');
    if (selected > info.need) throw new Error('指定数を超えて選べてしまう');

    // ちょうど選んだら回答できること
    btn = await page.locator('#q-card .rowbtns button').last();
    if (selected === info.need) {
      console.log('ちょうど選んだときのボタン:', (await btn.innerText()).trim(), '/ 押せるか:', await btn.isEnabled());
      if (!await btn.isEnabled()) throw new Error('ちょうど選んだのに回答できない');
    }
  }

  // 正解を選べば正解と判定されるか(3つ選択)
  await page.evaluate(() => {
    const q = examQuestions(currentExam).find(x => (x.n_correct || 1) === 3 && (x.type || 'choice') === 'choice');
    if (q) startSingleReview(q.id);
  });
  await page.waitForSelector('#q-card .opt');
  await require('./answer').answer(page, true);
  const banner = await page.locator('.resultbanner').innerText();
  console.log('3つ正解を選んだ結果:', banner.replace(/\n/g, ' ').slice(0, 30));
  if (!banner.includes('正解')) throw new Error('3つ選択の採点が壊れている');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
