// 出題された問題の形式を問わず回答するヘルパー。
// おまかせ出題ではマッチング/並び替えも出るため、選択式だけを前提にしない。
async function waitQuestion(page) {
  await page.waitForSelector('#q-card .opt, #q-card select', { timeout: 30000 });
}

// 選ぶだけ（模試では採点画面が途中に出ないので、待たずに次へ進む用）
async function choose(page, correct = false) {
  await waitQuestion(page);
  const type = await page.evaluate(() => (cur && cur.type) || 'choice');
  if (type === 'matching') {
    await page.evaluate((ok) => {
      cur.statements.forEach((s, i) => {
        const sel = document.getElementById('mt-' + i);
        const idx = ok ? [...sel.options].findIndex(o => o.text === s.answer) : 1;
        sel.selectedIndex = idx >= 0 ? idx : 1;
      });
    }, correct);
  } else if (type === 'ordering') {
    const idxs = await page.evaluate((ok) => {
      const items = ordItems(cur);
      return ok ? cur.order_answer.map(t => items.indexOf(t))
                : cur.order_answer.map((_, i) => i);
    }, correct);
    for (const i of idxs) await page.locator('#q-card .opt').nth(i).click();
  } else {
    const i = correct
      ? await page.evaluate(() => displayOpts(cur).findIndex(o => o.correct))
      : 0;
    await page.locator('#q-card .opt').nth(Math.max(0, i)).click();
  }
  await page.locator('#q-card button:has-text("回答する")').click();
}

// 回答して採点画面が出るまで待つ（練習モード用）
async function answer(page, correct = false) {
  await choose(page, correct);
  await page.waitForSelector('.resultbanner');
}

// 選択式だけの機能(シャッフル・キーボード操作)を試すときに使う。
// おまかせ出題ではマッチング/並び替えも出るため、選択式を明示的に開く
async function startChoiceQuestion(page) {
  await page.evaluate(() => {
    const q = examQuestions(currentExam).find(x => (x.type || 'choice') === 'choice');
    startSingleReview(q.id);
  });
  await page.waitForSelector('#q-card .opt');
}

module.exports = { waitQuestion, choose, answer, startChoiceQuestion };
