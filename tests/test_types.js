// マッチング・並び替え問題が出題・採点できるかのE2E
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errs = [];
  const b = await chromium.launch({ channel: 'msedge', headless: true });
  const p = await b.newPage({ viewport: { width: 420, height: 900 } });
  p.on('pageerror', e => errs.push(e.message));
  p.on('dialog', async d => await d.accept());
  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await p.goto(url);
  await p.waitForSelector('.examcard');
  await p.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await p.waitForSelector('#v-home.on');

  for (const t of ['matching', 'ordering']) {
    const id = await p.evaluate(tt => {
      const q = examQuestions(currentExam).find(x => x.type === tt);
      return q ? q.id : null;
    }, t);
    if (!id) { console.log(t, ': 該当なし'); continue; }
    await p.evaluate(i => startSingleReview(i), id);
    await p.waitForSelector('#q-card');

    if (t === 'matching') {
      const n = await p.locator('#q-card select').count();
      console.log('matching:', id, '/ プルダウン', n, '個');
      // 正解の組み合わせを選ぶ
      await p.evaluate(() => {
        cur.statements.forEach((s, i) => {
          const sel = document.getElementById('mt-' + i);
          const idx = [...sel.options].findIndex(o => o.text === s.answer);
          if (idx >= 0) sel.selectedIndex = idx;
        });
      });
    } else {
      const n = await p.locator('#q-card .opt').count();
      console.log('ordering:', id, '/ 選択肢', n, '個');
      // 表示順の中から、正解の順序に対応する位置を求めてタップする
      const idxs = await p.evaluate(() => {
        const items = ordItems(cur);
        return cur.order_answer.map(t => items.indexOf(t));
      });
      console.log('   正解の位置:', idxs.join(','));
      for (const i of idxs) await p.locator('#q-card .opt').nth(i).click();
      console.log('   選択済み:', await p.evaluate(() => ordSel.length), '/', await p.evaluate(() => cur.order_answer.length));
    }
    await p.locator('#q-card button:has-text("回答する")').click();
    await p.waitForSelector('.resultbanner');
    console.log('   採点結果:', (await p.locator('.resultbanner').innerText()).split('\n')[0]);
    const ex = await p.locator('#q-card .expl').count();
    console.log('   解説ブロック:', ex, '件');
  }
  console.log(errs.length ? 'JSエラー: ' + errs[0] : 'JSエラーなし');
  await b.close();
})();
