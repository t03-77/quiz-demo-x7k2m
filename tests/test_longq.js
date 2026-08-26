// 書き直しで問題文が長くなったため、最長クラスの問題でUIが崩れないか確認する
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } }); // iPhone相当の狭い画面
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('dialog', async d => { await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  await page.waitForSelector('#v-home.on');
  await page.locator('button:has-text("問題を解く")').click();

  // SAP-C02で最も問題文が長い問題を直接開く
  const info = await page.evaluate(() => {
    const qs = examQuestions(currentExam).filter(q => (q.type || 'choice') === 'choice');
    const q = qs.reduce((a, b) => (b.question.length > a.question.length ? b : a));
    startSingleReview(q.id);
    return { id: q.id, len: q.question.length, opts: q.options.length };
  });
  await page.waitForSelector('#q-card .opt');
  console.log('最長の問題:', info.id, info.len + '字', '選択肢' + info.opts + '個');

  // 横スクロールが発生していないか(はみ出しの検出)
  const overflow = await page.evaluate(() => ({
    doc: document.documentElement.scrollWidth,
    win: window.innerWidth,
    card: document.querySelector('#q-card').scrollWidth,
  }));
  console.log('画面幅', overflow.win, '/ 文書幅', overflow.doc, '/ カード幅', overflow.card);
  if (overflow.doc > overflow.win + 1) throw new Error('横方向にはみ出している');

  await page.screenshot({ path: 'long_q.png', fullPage: true });

  // 回答して解説まで表示されるか
  const i = await page.evaluate(() => displayOpts(cur).findIndex(o => o.correct));
  await page.locator('#q-card .opt').nth(i).click();
  await page.locator('#q-card button:has-text("回答する")').click();
  await page.waitForSelector('.resultbanner');
  const expl = await page.locator('.expl').first().innerText();
  console.log('解説の表示:', expl.length + '字');
  await page.screenshot({ path: 'long_q_result.png', fullPage: true });

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
