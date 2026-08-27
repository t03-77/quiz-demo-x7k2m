// 不具合報告の送信先。設定すると、報告シートに「送信する」ボタンが出る。
//
// 設定しない場合は「内容をコピーする」だけが出る（コピーしてメールやチャットで送ってもらう形）。
//
// ■ メールで受け取りたいとき（メールアドレスは公開されません）
//   1. https://formspree.io/ に登録し、そこで**自分のメールアドレス**を設定する
//   2. 発行されたエンドポイント（https://formspree.io/f/xxxxxxx）を下に書く
//   3. git add data/report.js && git commit && git push
//
//   アプリに載るのはエンドポイントIDだけで、メールアドレスは Formspree 側が保持します。
//   報告が届くと Formspree があなたのメールに転送します。
//
//   ※ このIDは公開されるため、いたずら送信を受ける可能性はあります。
//      Formspree 側にスパム対策と件数上限（無料枠は月50件）があります。
//
// window.REPORT_ENDPOINT = 'https://formspree.io/f/xxxxxxx';
