// データ整合スモークテスト: アプリのレンダラーが期待する形状を全問検証する
const fs = require('fs');
const path = require('path');
const base = path.join(__dirname, '..');

global.window = {};
eval(fs.readFileSync(path.join(base, 'data', 'exams.js'), 'utf8'));
eval(fs.readFileSync(path.join(base, 'data', 'orig.js'), 'utf8'));
const EXAMS = window.EXAMS, ORIG = window.ORIG_QUESTIONS;
const officialRaw = JSON.parse(fs.readFileSync(path.join(base, '資料', '変換済み', 'questions_all.json'), 'utf8'));
const OFFICIAL = officialRaw.questions;

const examIds = new Set(EXAMS.map(e => e.id));
let errors = [];
function checkQ(q, src) {
  if (!examIds.has(q.exam)) errors.push(`${src} ${q.id}: 未知の試験 ${q.exam}`);
  if (!q.question || !q.question.trim()) errors.push(`${src} ${q.id}: 問題文なし`);
  if (!['orig', 'qset', 'exam', 'pretest'].includes(q.set)) errors.push(`${src} ${q.id}: 未知のセット ${q.set}`);
  if (q.type === 'choice' || !q.type) {
    if (!Array.isArray(q.options) || q.options.length < 2) return errors.push(`${src} ${q.id}: options不正`);
    const nc = q.options.filter(o => o.correct).length;
    if (nc !== q.n_correct || nc === 0) errors.push(`${src} ${q.id}: correct数不一致`);
    for (const o of q.options) if (!o.letter || !o.text) errors.push(`${src} ${q.id}: 選択肢欠落`);
  } else if (q.type === 'matching') {
    if (q.needs_review) return;
    if (!Array.isArray(q.statements) || !q.statements.length) return errors.push(`${src} ${q.id}: statements不正`);
    for (const s of q.statements) if (!s.statement || !s.answer) errors.push(`${src} ${q.id}: statement欠落`);
  } else if (q.type === 'ordering') {
    if (q.needs_review) return;
    if (!Array.isArray(q.order_answer) || q.order_answer.length < 2) errors.push(`${src} ${q.id}: order_answer不正`);
  } else errors.push(`${src} ${q.id}: 未知タイプ ${q.type}`);
}
ORIG.forEach(q => checkQ(q, 'orig'));
OFFICIAL.forEach(q => checkQ(q, 'official'));

// ID重複(ORIG+OFFICIAL統合後)
const ids = ORIG.map(q => q.id).concat(OFFICIAL.map(q => q.id));
if (new Set(ids).size !== ids.length) errors.push('ID重複あり');

// 試験ごとの統合プール件数
console.log('試験別プール(オリジナル+公式):');
for (const e of EXAMS) {
  const o = ORIG.filter(q => q.exam === e.id).length;
  const f = OFFICIAL.filter(q => q.exam === e.id && !q.needs_review).length;
  console.log(`  ${e.id}: ${o + f}問 (orig ${o} + official ${f})`);
}
console.log(errors.length ? `NG ${errors.length}件:` : '全チェックOK');
errors.slice(0, 20).forEach(e => console.log(' ', e));
process.exit(errors.length ? 1 : 0);
