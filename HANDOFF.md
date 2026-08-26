# 引き継ぎメモ（2026-08-26 時点）

別のAI・別セッションが続きを行うための現状整理。まずこのファイルを読んでから作業すること。

## このプロジェクトは何か

AWS認定資格の学習ウェブアプリ。静的HTML1枚（`index.html`）＋データファイル（`data/*.js`）で動く。
サーバー不要。`index.html` をブラウザで開けば使える。

- 仕様: `docs/仕様書.md`
- 使い方・ツール一覧: `README.md`
- 公開先: https://t03-77.github.io/quiz-demo-x7k2m/ （※未プッシュのため現在は旧版）

## データの二層構成（重要・著作権対応）

| 種別 | 場所 | サイトに同梱 |
|---|---|---|
| オリジナル問題 1271問（自作） | `data/orig.js` | **する** |
| AWS公式問題 1310問 | `資料/変換済み/questions_all.json` | **しない**（利用者が手元のファイルを読み込む方式） |
| 読み上げ音声 | `audio/` | **しない**（公式問題の読み上げのため） |

`資料/` と `audio/` は `.gitignore` 済み。**この方針は崩さないこと。**

## 現在の到達状況

- オリジナル問題: **1271問**（現役10資格 × 各100問 + AIP-C01）
- 解説の質: **全11資格が公式模試の水準に到達**（`python tools/audit_explanations.py` で確認可能）
- ドメイン配分: **全11資格が公式試験ガイドの比重と整合**（`python tools/audit_domains.py`）
- 実装済み: 演習・模擬試験（本番の問題数/時間/合格スコア）・間隔反復SRS・分野別弱点分析・
  選択肢シャッフル・キーボード操作・AI連携（質問/用語深掘り/問題のAI変換/予算上限）・読み上げ音声

## 未完了の作業（優先度順）

1. **AIP-C01の本番形式が50問しかない**（目標100問）。`資料/生成/AIP-C01_orig_b2.json` に301〜350がある。
   351〜400を `AIP-C01_orig_b3.json` 以降に追加する。既存221問は一問一答形式で `set: "flash"` として分離済み
2. **マッチング・並び替え形式の問題がない**。公式模試には各1%含まれる。
   スキーマは `資料/変換済み/questions_all.json` 内の `type: "matching"` / `"ordering"` を参照
3. **3つ選択の問題がない**（公式は2%）。複数選択は2つ選択が20%で公式11%よりやや多い
4. ~~PWA化~~ **完了**（`sw.js` / `manifest.webmanifest` / `icon.svg`。オフラインで演習・採点まで動作確認済み。
   音声は容量が大きいのでキャッシュ対象外にしている。
   注意: キャッシュから起動すると `navigator.onLine` が true を返すため、
   オフライン判定は `audio/` 配下（SWが素通しするパス）へのfetchで実測している）
5. **図解が未着手**（仕様書のM4）
6. **AIP-C01以外の読み上げ音声が未生成**
7. **AI機能を実際のAPIキーで未検証**。テストはすべて模擬応答。ブラウザ直呼び出しのCORSは
   `anthropic-dangerous-direct-browser-access` ヘッダーで対応済みだが実キーでの確認が必要
8. **GitHubへのプッシュが未実行**。認証が通らずローカルに30以上のコミットが溜まっている。
   ユーザーが手動で `git push origin main` する必要がある

## 作業の進め方

### 問題を追加・修正したら必ず
```
python tools/build_orig_data.py      # 資料/生成/*.json → data/orig.js
node tools/smoke_test.js             # データ整合
python tools/audit_consistency.py    # 解説と正誤フラグの矛盾
python tools/audit_domains.py        # ドメイン配分が公式比重と合っているか
python tools/audit_explanations.py   # 解説が公式水準か
```

### 問題を生成・書き直すときの必須事項（過去に失敗した点）

1. **お手本には公式の解説本文まで含める**。`資料/校正サンプル/{EXAM}.md` がそれ。
   問題文と選択肢だけ渡すと、生成される解説が公式の半分以下になる（実際にそうなった）
2. **公式解説は字数の約半分がURL誘導**。字数をそのまま目標にすると2倍に膨らんだ基準を追うことになる。
   `audit_explanations.py` はURLと誘導文を除いて比較している
3. **サブエージェントを多数起動しない**。同時実行の上限に繰り返し当たって失敗した。
   1体ずつ、10問ごとにファイル保存させること
4. **保護フィールドを変えない**。解説の書き直しでは `explanation` 以外
   （id/exam/set/type/domain/level/question/n_correct/options[].letter/text/correct）に触れないこと
5. 中断でファイルに反映されない成果が出たら `python tools/merge_explanation_chunks.py` で回収できる

### E2Eテスト
`C:\Users\na7sh\AppData\Local\Temp\quizapp_e2e\` に playwright-core 導入済み。
`node test.js` `node test_mock.js` `node test_uxfix.js` など。
実行は `chromium.launch({channel:'msedge'})`（ブラウザは別途インストール不要）。

## 品質検証で分かっていること

- 公式ドキュメントで**実際に裏を取ったのは22問**（1件の誤りを発見・修正済み）。
  残り約1250問は機械的検査のみ。AI生成である以上、数%の誤りが残る可能性がある
- 機械的検査はすべてクリア: 解説と正誤フラグの矛盾0件、水増し0件、ドメイン配分整合
- 誤りが出やすいパターンは**「対応するのはA、B、C」型の列挙**（唯一の実誤りがこれだった。
  S3イベント通知の送信先からEventBridgeが抜けていた）。`audit_enumerations.py` で候補を出せる

## 環境メモ

- Windows。PowerShellはBOM問題があるため、日本語を含むファイルの書き込みは
  PowerShellの `Set-Content` ではなく Write ツールか Python を使うこと
- Python は `python`、Node は `node` で動く。`$env:PYTHONIOENCODING="utf-8"` を付けないと文字化けする
