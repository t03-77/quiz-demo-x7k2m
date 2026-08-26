// 間隔反復(SRS)のE2E
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
  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.waitForSelector('#v-home.on');

  // 2連続正解 → 習得済み + due が設定されるか (直接ロジックを検証)
  const r = await page.evaluate(() => {
    const id = pool()[0].id;
    const st = {attempts: [], streak: 0};
    // 1回目正解
    st.attempts.push({correct: true}); st.streak = 1; applySrs(st, true);
    const s1 = statusOf(st), due1 = st.due;
    // 2回目正解 → 習得、due=1日後
    st.attempts.push({correct: true}); st.streak = 2; applySrs(st, true);
    const s2 = statusOf(st), gap1 = Math.round((st.due - Date.now()) / 86400000);
    // 3回目正解 → 次は3日後
    st.attempts.push({correct: true}); st.streak = 3; applySrs(st, true);
    const gap2 = Math.round((st.due - Date.now()) / 86400000);
    // 期限を過去にする → 復習期
    st.due = Date.now() - 1000;
    const s3 = statusOf(st);
    // 間違える → リセット
    st.streak = 0; applySrs(st, false);
    const s4 = statusOf(st), dueAfterMiss = st.due;
    return {s1, due1, s2, gap1, gap2, s3, s4, dueAfterMiss, id};
  });
  console.log('1回正解:', r.s1, '/ due設定なし:', r.due1 === undefined || r.due1 === null);
  console.log('2回連続正解:', r.s2, '→ 次の復習まで', r.gap1, '日 (期待1)');
  console.log('3回連続正解: 次の復習まで', r.gap2, '日 (期待3)');
  console.log('期限到来:', r.s3, '(期待: 復習期)');
  console.log('不正解でリセット:', r.s4, '/ due解除:', r.dueAfterMiss === null);

  // 復習期の問題が出題優先されるか
  const picked = await page.evaluate(() => {
    const ids = pool().map(q => q.id);
    // 3問を「復習期」に、1問を「未出題」のまま
    for (let i = 0; i < 3; i++) {
      P.questions[ids[i]] = {attempts: [{correct: true}], streak: 2,
        due: Date.now() - 86400000, srs: 1, lastIndex: -999};
    }
    P.history = new Array(10).fill(0).map(() => ({id: 'x', correct: true}));
    return {next: pickNext('auto'), isDue: [ids[0], ids[1], ids[2]].includes(pickNext('auto'))};
  });
  console.log('おまかせで復習期が優先されたか:', picked.isDue);

  // ホームの通知とドーナツ
  await page.evaluate(() => refreshHome());
  const note = await page.locator('#h-duenote').innerText();
  console.log('ホーム通知:', note || '(なし)');
  await page.locator('nav button[data-v="stats"]').click();
  await page.waitForSelector('#donut circle');
  const legend = await page.locator('#donut-legend').innerText();
  console.log('ドーナツ内訳:', legend.replace(/\n/g, ' / '));
  await page.screenshot({ path: '13_srs.png' });

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
