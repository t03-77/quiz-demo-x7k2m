/* デモ用のAPIキーをパスワードで暗号化して data/demo_key.js を作る
 *
 * 用途: 会社などで同僚に触ってもらうとき、URLとパスワードだけ渡せばAI機能を試せるようにする。
 *
 * 【重要・必ず守ること】
 *  1. **デモ専用のAPIキーを新規発行**して使う。普段使いのキーは絶対に使わない
 *  2. 提供元の管理画面で、そのキーに**低い上限額**を設定する（$1〜5程度）
 *  3. **デモが終わったらキーを無効化**する
 *  4. パスワードは**20文字以上のランダム文字列**にする
 *
 * 暗号文は公開サイトに置かれるため、手元で総当たり攻撃を試せてしまう。
 * サーバー側で回数制限がかけられないので、パスワードの強度がそのまま防御力になる。
 * 上の4点を守れば、最悪破られても損害は上限額までに収まる。
 *
 * 使い方:
 *   node tools/make_demo_key.js "sk-ant-xxxxx" "20文字以上のパスワード" [ワークスペースID]
 *
 * ワークスペースに紐づいたキーの場合は、第3引数に wrkspc_ から始まるIDを渡す。
 * これを入れておけば、受け取った人は設定をいじらずに使える。
 * （IDは秘密情報ではないので暗号化せずに持たせる）
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const [apiKey, password, workspace] = process.argv.slice(2);

if (!apiKey || !password) {
  console.error('使い方: node tools/make_demo_key.js "<APIキー>" "<パスワード>" [ワークスペースID]');
  process.exit(1);
}
if (workspace && !/^wrkspc[_-]/.test(workspace)) {
  console.error('ワークスペースIDは wrkspc_ で始まる文字列です。渡された値: ' + workspace);
  process.exit(1);
}
if (password.length < 20) {
  console.error('パスワードが短すぎます（20文字以上にしてください）。');
  console.error('暗号文は公開サイトに置かれ、手元で総当たりを試せてしまうためです。');
  process.exit(1);
}
if (!/^sk-/.test(apiKey)) {
  console.error('APIキーの形式が違うようです（sk- で始まるはずです）。');
  process.exit(1);
}

const ITER = 600000;          // 総当たりを遅くするための反復回数
const salt = crypto.randomBytes(16);
const iv = crypto.randomBytes(12);
const dk = crypto.pbkdf2Sync(password, salt, ITER, 32, 'sha256');
const cipher = crypto.createCipheriv('aes-256-gcm', dk, iv);
const enc = Buffer.concat([cipher.update(apiKey, 'utf8'), cipher.final()]);
const tag = cipher.getAuthTag();

const b64 = b => Buffer.from(b).toString('base64');
const payload = {
  v: 1, iter: ITER,
  salt: b64(salt), iv: b64(iv),
  data: b64(Buffer.concat([enc, tag])),
};
if (workspace) payload.workspace = workspace;   // 秘密ではないので平文で持たせる

const out = path.resolve(__dirname, '..', 'data', 'demo_key.js');
fs.writeFileSync(out,
  '// デモ用APIキー（パスワードで暗号化済み）。tools/make_demo_key.js で生成\n' +
  '// このファイルは公開される。デモ専用キー・低い上限額・使用後は無効化 を必ず守ること\n' +
  'window.DEMO_KEY = ' + JSON.stringify(payload) + ';\n', 'utf8');

console.log('作成しました: data/demo_key.js');
console.log('  キーの先頭:', apiKey.slice(0, 10) + '...');
console.log('  反復回数  :', ITER.toLocaleString());
console.log('  ワークスペース:', workspace || '(指定なし)');
if (!workspace && /^sk-ant/.test(apiKey)) {
  console.log();
  console.log('  ※ 「anthropic-workspace-id is required」というエラーが出る場合は、');
  console.log('     第3引数に wrkspc_ から始まるIDを渡して作り直してください。');
  console.log('     入れておけば、受け取った人は設定をいじらずに使えます。');
}
console.log();
console.log('このあとの手順:');
console.log('  1. 提供元の管理画面で、このキーに低い上限額（$1〜5）を設定する');
console.log('  2. 公開する場合のみ、意図的にコミットする:');
console.log('       git add -f data/demo_key.js   ← .gitignore に入れてあるので -f が要る');
console.log('       git commit -m "デモ用キーを配布" && git push');
console.log('  3. 同僚にはURLとパスワードを渡す');
console.log('       設定 → AI連携 → デモモードにチェック → パスワードを入れて解錠');
console.log('  4. **デモが終わったら、キーを無効化して data/demo_key.js を削除する**');
console.log('       git rm data/demo_key.js && git commit && git push');
console.log();
console.log('  ※ 暗号文は公開されるため、キーを無効化するまでが1セットです。');
console.log('    ファイルを消してもGitの履歴には残るので、必ず提供元でキーを無効化してください。');
