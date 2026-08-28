// 出題セットの選択が「選ぶ意味があるときだけ」出ることを確認する
// 種類が1つしかないと「すべて105 / 本番形式105」と同じ数が並び、迷わせるだけになる
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

  // SAP-C02 は本番形式しかない → カードごと出ないこと
  await page.locator('.examcard', { hasText: 'Solutions Architect – Professional' }).first().click();
  await page.waitForSelector('#v-home.on');
  const sapVisible = await page.locator('.card:has(#h-sets)').isVisible();
  const sapKinds = await page.locator('#h-sets .chip').count();
  console.log('SAP-C02  種類の数:', sapKinds, '/ カードの表示:', sapVisible ? '★出ている' : '出ない（正しい）');
  if (sapVisible) throw new Error('選ぶ意味がないのに出題セットの選択が出ている');

  // AIP-C01 は本番形式と一問一答がある → 出ること
  await page.locator('nav button[data-v="exams"]').click();
  await page.locator('.examcard', { hasText: 'AIP' }).first().click();
  await page.waitForSelector('#v-home.on');
  const aipVisible = await page.locator('.card:has(#h-sets)').isVisible();
  const chips = await page.locator('#h-sets .chip').allInnerTexts();
  console.log('AIP-C01  種類:', chips.join(' / '), '→ カードの表示:', aipVisible ? '出る（正しい）' : '★出ない');
  if (!aipVisible) throw new Error('複数の種類があるのに選べない');

  // 問題数の選択は常にあること
  console.log('1セットの問題数:', await page.locator('#home-seslen').count() > 0 ? 'あり' : '★なし');

  console.log(errors.length ? 'JSエラー ' + errors[0] : 'JSエラーなし');
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('失敗:', e.message); process.exit(1); });
