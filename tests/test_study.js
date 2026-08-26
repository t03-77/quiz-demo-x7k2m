// 選択肢シャッフル + 分野別弱点分析のE2E
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

  // シャッフルON
  await page.locator('nav button[data-v="settings"]').click();
  await page.locator('#set-shuffle').check();

  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.locator('button:has-text("問題を解く")').click();
  await require('./answer').startChoiceQuestion(page);   // シャッフルは選択式のみ対象

  // 表示記号は連番、テキストの並びは元と変わっているはず
  const shown = await page.locator('#q-card .opt').evaluateAll(els =>
    els.map(e => ({ letter: e.querySelector('.lt').textContent, text: e.textContent.slice(1, 25) })));
  console.log('表示記号:', shown.map(s => s.letter).join(','));
  const qid = await page.evaluate(() => cur.id);
  const origOrder = await page.evaluate(id => byId(id).options.map(o => o.text.slice(0, 24)), qid);
  const shownText = shown.map(s => s.text.trim());
  const same = origOrder.every((t, i) => shownText[i] && shownText[i].startsWith(t.slice(0, 10)));
  console.log('元の順序と同一か:', same, '(falseならシャッフル成功)');

  // 正解を選んで採点が正しいか
  const correctIdx = await page.evaluate(id => displayOpts(byId(id)).findIndex(o => o.correct), qid);
  await page.locator('#q-card .opt').nth(correctIdx).click();
  await page.locator('#q-card button:has-text("回答する")').click();
  await page.waitForSelector('.resultbanner');
  const banner = await page.locator('.resultbanner').innerText();
  console.log('結果:', banner.replace(/\n/g, ' '));
  if (!banner.includes('正解')) throw new Error('シャッフル時の採点が壊れている');

  // さらに数問解いて分野別統計を出す
  for (let i = 0; i < 5; i++) {
    await page.locator('#q-card .rowbtns button').last().click();
    await require('./answer').answer(page);
  }
  await page.locator('nav button[data-v="stats"]').click();
  await page.waitForSelector('#domstats .weakitem');
  const doms = await page.locator('#domstats .weakitem').allInnerTexts();
  console.log('分野別統計:', doms.length + '分野');
  doms.slice(0, 3).forEach(d => console.log('  ', d.replace(/\n/g, ' ')));

  // 分野をタップ → その分野だけの復習が始まるか
  await page.locator('#domstats .weakitem').first().click();
  await require('./answer').waitQuestion(page);
  const tags = await page.locator('#q-card .tag').allInnerTexts();
  console.log('分野別復習タグ:', tags.find(t => t.includes('分野別')) || '(なし)');
  const inDomain = await page.evaluate(() => cur.domain === domFilter);
  console.log('出題が対象分野に一致:', inDomain);

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
