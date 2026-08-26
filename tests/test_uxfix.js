// UIレビュー指摘の修正を検証
const { chromium } = require('playwright-core');
const path = require('path');
const { waitQuestion, answer } = require('./answer');

(async () => {
  const errors = [], dialogs = [];
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push(e.message));
  page.on('dialog', async d => { dialogs.push(d.message()); await d.accept(); });

  const url = 'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');

  // #10 0問の試験(ANS)は無効化されているか
  const ans = page.locator('.examcard', { hasText: 'Advanced Networking' });
  console.log('ANSカードに onclick:', await ans.getAttribute('onclick') === null ? 'なし(無効化OK)' : '← まだ押せる');
  console.log('ANS表示:', (await ans.innerText()).replace(/\n/g, ' ').slice(0, 60));

  await page.locator('.examcard', { hasText: 'Solutions Architect – Associate' }).first().click();
  await page.waitForSelector('#v-home.on');

  // #3 現在地: ホーム表示中は「学習」タブが点灯するか
  const lit = await page.locator('nav button.on').innerText();
  console.log('ホーム表示中に点灯するタブ:', lit.replace(/\n/g, ''));

  // #1 セッションの区切り: 10問でまとめが出るか
  await page.locator('button:has-text("問題を解く")').click();
  await waitQuestion(page);
  console.log('問題ヘッダ:', (await page.locator('#q-card .qmeta').innerText()).replace(/\n/g, ' | '));
  for (let i = 0; i < 10; i++) {
    await answer(page);
    await page.locator('#q-card .rowbtns button').last().click();
  }
  await page.waitForSelector('.resultbanner');
  console.log('10問後:', (await page.locator('.resultbanner').innerText()).replace(/\n/g, ' '));
  const hasAgain = await page.locator('button:has-text("もう1セット")').count();
  console.log('「もう1セット」ボタン:', hasAgain ? 'あり' : '← なし');

  // #8 採点画面: 不正解の解説が折りたたまれているか
  await page.locator('#q-card .weakitem').first().click();
  await page.waitForSelector('.expl');
  const openExpl = await page.locator('#q-card .expl:not(details)').count();
  const folded = await page.locator('#q-card details.expl').count();
  console.log(`採点画面の解説: 展開${openExpl}件 / 折りたたみ${folded}件`);

  // #4 模試中にナビを押すと確認が出るか
  await page.locator('button:has-text("結果一覧へ戻る")').click();
  await page.locator('button:has-text("学習トップへ")').click();
  await page.waitForSelector('#v-home.on');
  await page.locator('.chip:has-text("ウォームアップ")').click();
  await waitQuestion(page);
  dialogs.length = 0;
  await page.locator('nav button[data-v="exams"]').click();
  await page.waitForTimeout(300);
  console.log('模試中にナビ移動 → 確認ダイアログ:', dialogs.length ? 'あり: ' + dialogs[0].slice(0, 40) : '← なし');

  console.log(errors.length ? 'JSエラー: ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('E2E失敗:', e.message); process.exit(1); });
