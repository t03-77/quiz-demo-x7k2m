// 問題が消えたときに統計がどうなるかを確認する
// 出題されなくなった問題の成績が正答率に混ざると、実力を見誤るため集計から外している
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

  // 履歴を仕込む: 実在する問題2問(正解1/不正解1) + すでに消えた問題2問(いずれも正解)
  const seeded = await page.evaluate(() => {
    const ids = examQuestions(currentExam).slice(0, 2).map(q => q.id);
    P = { questions: {}, history: [
      { id: ids[0], date: '2026-08-01', correct: true },
      { id: ids[1], date: '2026-08-01', correct: false },
      { id: 'SAA-C03_orig_deleted_1', date: '2026-08-01', correct: true },
      { id: 'SAA-C03_orig_deleted_2', date: '2026-08-01', correct: true },
    ]};
    saveP(); refreshHome();
    return { live: ids, total: P.history.length };
  });
  console.log('仕込んだ履歴:', seeded.total + '件(うち2件は存在しない問題)');

  const rate = await page.locator('#h-rate').innerText();
  const count = await page.locator('#h-count').innerText();
  console.log('ホーム表示 → 延べ回答:', count, '/ 正答率:', rate);
  if (count !== '2') throw new Error('存在しない問題が延べ回答に含まれている (期待2, 実際' + count + ')');
  if (rate !== '50%') throw new Error('正答率が実在する問題だけで計算されていない (期待50%, 実際' + rate + ')');

  // 統計画面も同じ扱いか
  await page.locator('nav button[data-v="stats"]').click();
  await page.waitForSelector('#s-rate');
  const sRate = await page.locator('#s-rate').innerText();
  const sCount = await page.locator('#s-count').innerText();
  console.log('統計画面   → 延べ回答:', sCount, '/ 正答率:', sRate);
  if (sCount !== '2' || sRate !== '50%') throw new Error('統計画面の集計が揃っていない');

  // 履歴データ自体は消えていないこと(問題が戻れば集計にも戻る)
  const kept = await page.evaluate(() => P.history.length);
  console.log('保存されている履歴:', kept + '件（消さずに残している）');
  if (kept !== 4) throw new Error('履歴が削除されてしまっている');

  console.log(errors.length ? 'JSエラー ' + errors.length + '件: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
