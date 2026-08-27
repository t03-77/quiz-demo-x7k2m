# 引き継ぎメモ

別のAI・別セッションが続きを行うための現状整理。

> **先に `CLAUDE.md` を読むこと。** 問題を作る・直すときの決まりが書いてある。
> 同じ失敗を繰り返さないための鉄則7つと、環境の落とし穴をまとめてある。
> このファイル（HANDOFF.md）は「いま何がどこまで終わっているか」を書く。

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

- オリジナル問題: **1399問**（全11資格。AIP-C01は本番形式106問＋一問一答221問）
- 解説の質: **全11資格が公式模試の水準に到達**（`python tools/audit_explanations.py` で確認可能）
- ドメイン配分: **全11資格が公式試験ガイドの比重と整合**（`python tools/audit_domains.py`）
- 問題文の分量: **全11資格で公式模試の下位10%を下回る問題が0問**（下記「実測で見つかった品質ギャップ」参照）
- 試験範囲: 公式模試で正解として問われるサービスの**未カバーは解消**
- 実装済み: 演習・模擬試験（本番の問題数/時間/合格スコア）・間隔反復SRS・分野別弱点分析・
  選択肢シャッフル・キーボード操作・AI連携（質問/用語深掘り/問題のAI変換/予算上限）・読み上げ音声・PWA
- E2Eテスト13本すべて合格（`tests/`。最長400字の問題文でも横方向のはみ出しなし）

## 未完了の作業（優先度順）

1. **3つ選択の問題がない**（公式は2%）。複数選択は2つ選択が20%で公式11%よりやや多い
2. **図解が未着手**（仕様書のM4）
3. **AIP-C01以外の読み上げ音声が未生成**。
   音声は `genai_dev_pro/official/questions_official.json`（公式問題）から生成しており、
   `data/orig.js` の自作問題とは生成元が別。**自作問題を書き直しても音声の作り直しは不要**
4. **AI機能を実際のAPIキーで未検証**。テストはすべて模擬応答。ブラウザ直呼び出しのCORSは
   `anthropic-dangerous-direct-browser-access` ヘッダーで対応済みだが実キーでの確認が必要
5. **GitHubへのプッシュが未実行**。認証が通らずローカルに37以上のコミットが溜まっている。
   ユーザーが手動で `git push origin main` する必要がある

### 完了した項目（記録）
- ~~AIP-C01の本番形式100問~~ **完了**（106問。ID 301〜400が連番で欠番なし）
- ~~マッチング・並び替え形式~~ **完了**（各15問）
- ~~PWA化~~ **完了**（`sw.js` / `manifest.webmanifest` / `icon.svg`。オフラインで演習・採点まで動作確認済み。
  音声は容量が大きいのでキャッシュ対象外。
  注意: キャッシュから起動すると `navigator.onLine` が true を返すため、
  オフライン判定は `audio/` 配下（SWが素通しするパス）へのfetchで実測している）

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

### E2Eテスト（15本、すべて合格状態）
テスト本体は `tests/` にある。実行するには playwright-core が要る:
```
cd %TEMP% && mkdir quizapp_e2e && cd quizapp_e2e
npm init -y && npm i playwright-core
copy <プロジェクト>\tests\* .
node test.js
```
`chromium.launch({channel:'msedge'})` で動く（ブラウザの別途インストール不要）。

**重要**: `answer.js` が共通ヘルパー。出題はマッチング・並び替えも混ざるため、
`.opt`（選択式のUI）だけを前提にしたテストは失敗する。必ず次を使うこと:
- `waitQuestion(page)` … 形式を問わず問題の表示を待つ
- `answer(page, correct)` … 形式を問わず回答して採点画面まで
- `choose(page)` … 回答だけ（模試は途中で採点画面を出さないのでこちら）
- `startChoiceQuestion(page)` … 選択式限定の機能（シャッフル・キーボード）を試すとき

## 実測で見つかった品質ギャップ（2026-08-27・**対応済み**）

> 以下は問題の記録。**2項目とも解消済み**。同じ検査を再実行すれば確認できる（測り方は各節の末尾）。
> 到達値: 分量は下限割れ0問（中央値は公式比 77〜152%、最低はAIF-C01の82%）、
> 未カバー領域は0種（検出上2種残るが、いずれも表記ゆれによる誤検出。実データで確認済み）。


利用者の要求は「公式模試と同等かやや難しい水準」「試験範囲を満遍なく」。
これを機械的に測ったところ、次の2つが未達だった。

### 1. 問題文の分量が公式模試に届いていない

資格ごとに公式模試（`set` が `exam`/`pretest`）の問題文長と比較した結果:

| 資格 | 公式の中央値 | 自作の中央値 | 公式比 | 公式の下位10%を下回る問題 |
|---|---|---|---|---|
| SAP-C02 | 353字 | 255字 → **321字** | 72% → **91%** | 41問 → **0問** |
| DOP-C02 | 323字 | 241字 → **310字** | 74% → **96%** | 10問 → **0問** |
| SCS-C03 | 256字 | 199字 → **221字** | 77% → **86%** | 24問 → **0問** |
| DVA-C02 | 230字 | 188字 → **202字** | 81% → **87%** | 17問 → **0問** |
| AIF-C01 | 120字 | 97字 → **100字** | 80% → **82%** | 6問 → **0問** |
| DEA/SAA/AIP/MLA | — | — | 84〜85% → **85〜91%** | 各3〜10問 → **0問** |
| SOA-C03 | 217字 | 220字 → **229字** | 101% → 105% | 4問 → **0問** |
| CLF-C02 | 74字 | 112字 | 152% | 0問 |

対象127問の一覧は `資料/生成/_short_questions.json`（作業当時のもの。再検査は下記コマンドで）。

再検査のコマンド:
```
python -X utf8 -c "
import json,statistics
off=json.load(open(r'資料/変換済み/questions_all.json',encoding='utf-8'))
if isinstance(off,dict): off=off.get('questions',off)
js=open('data/orig.js',encoding='utf-8').read(); n=json.loads(js[js.index('['):js.rindex(']')+1])
for ex in sorted(set(q['exam'] for q in n)):
    o=sorted(len(q.get('question','')) for q in off if q.get('exam')==ex and q.get('set') in ('exam','pretest'))
    if not o: continue
    m=[len(q['question']) for q in n if q['exam']==ex and q.get('set')=='orig']
    print(ex, statistics.median(m), statistics.median(o), sum(1 for x in m if x<o[int(len(o)*.1)]))
"
```

**字数を増やすだけでは逆効果**。公式模試の問題文が長いのは、既存構成・定量的制約
（RTO/RPO、レイテンシ、規模、コスト上限）・評価軸が書かれていて、
それが正解を選ぶ根拠になっているため。飾りを足すのは水増しであり、やってはいけない。

### 2. 試験範囲に一度も触れていない領域がある

公式模試で**正解として問われる**のに、自作問題に一度も登場しないサービス
（カッコ内は公式模試で正解として問われた問題数）:

| 資格 | 未カバーだった領域 | 対応 |
|---|---|---|
| DOP-C02 | WAF(16) / EC2 Auto Scaling(6) / Step Functions(2) / IAM Identity Center(2) / RAM(2) / Firewall Manager(2) | `DOP-C02_orig_gap1.json` 12問 |
| SOA-C03 | EKS(6) / EC2 Auto Scaling(4) / RAM(3) / ECS(3) / SSM Parameter Store(2) / PrivateLink(2) / Backup Audit Manager(2) / SES(2) | `SOA-C03_orig_gap1.json` 16問 |
| SCS-C03 | EFS(2) / Fault Injection Service(2) / SQS(2) | `SCS-C03_orig_gap1.json` 6問 |
| MLA-C01 | Comprehend(5) / Kendra(2) | `MLA-C01_orig_gap1.json` 4問 |
| SAA-C03 | ECS(2) | `SAA-C03_orig_gap1.json` 2問 |
| AIF-C01 / CLF-C02 / DEA-C01 | EC2 / Client VPN / WAF | 各 `*_orig_gap1.json` 2問 |
| AIP-C01 / DVA-C02 | （誤検出。WebSocketは1問、REST APIは12問すでにあった） | 対応不要 |

全一覧は `資料/生成/_coverage_gaps.json`（作業当時のもの）。
SAA-C03 でコンテナ（ECS）が一問も出ないなど、明確な欠落だった。

**Amazon Kendra の注意**: 2026年6月30日にメンテナンスモード入り、7月30日から新規顧客受付終了。
MLA-C01 の試験ガイドには対象として残っているため出題しているが、
問題のシナリオは「すでに運用している」前提に統一し、新規構築を推奨する記述は避けている。

**この測り方の注意**: サービス名は表記ゆれが激しく、`Amazon`/`AWS` の前置を要求すると
大量の偽陽性が出る（自作側は "CloudWatch" と前置なしで書くため「未カバー」に見える）。
略称の展開（Simple Queue Service → SQS など）と、正解の選択肢に絞った集計が必須。

## 品質検証で分かっていること

- 公式ドキュメントで**精読したのは既存101問**。加えて今回追加した約60問は作成時に裏取りしている。
  残りは機械的検査のみ。AI生成である以上、数%の誤りが残る可能性がある
- 機械的検査はすべてクリア: 解説と正誤フラグの矛盾0件、水増し0件、ドメイン配分整合
- **誤りが出やすいパターンは「対応するのはA、B、C」型の列挙**。
  これまで見つかった実際の誤りは**4件すべてがこの型**だった:
  - S3イベント通知の送信先から EventBridge が抜けていた
  - CloudWatch高解像度アラームの期間から 20秒 が抜けていた（10秒/30秒だけ書いていた）
  - Trusted Advisor のカテゴリが5つになっていた（正しくは6つ。運用上の優秀性が欠落）
  - Bedrock ガードレールのポリシーから 自動推論チェック が抜けていた
- **1件見つけたら全問を横断して同じ誤りを直すこと**。上記3件は指摘が6箇所だったが、
  正規表現で全問走査したところ**8箇所**あった（`tools/fix_enumeration_gaps.py` がその実装）。
  候補の抽出は `audit_enumerations.py`

### カバレッジや分量を測るときの落とし穴（実際に踏んだ）

- **サービス名の表記ゆれ**。公式模試は「Amazon CloudWatch」、自作は「CloudWatch」と書くことが多い。
  `Amazon`/`AWS` の前置を要求して照合すると、カバー済みのものが大量に「未カバー」と出る。
  略称の展開（Simple Queue Service → SQS）と、正解の選択肢に絞った集計が必須。
  **機械的な検出結果は必ず実データで裏を取ること**（ありもしない穴を埋める無駄が発生する）
- **資格をまたいで分量を比較しない**。CLF-C02の公式模試は中央74字、SAP-C02は353字と4倍以上違う。
  全資格をまとめて基準を作ると、基礎資格が不当に「短すぎる」と判定される
- **問題文を長くするだけでは逆効果**。公式模試の問題文が長いのは、制約が具体的で
  それが正解を選ぶ根拠になっているため。飾りを足すのは水増し。
  書き足した制約が正解と噛み合い、できれば有力な誤答肢を排除できることを確認する
- **書き直しでは `question` 以外を変えていないことを機械的に確認する**。
  前回コミットの `data/orig.js` と全件突き合わせるのが確実（`git show HEAD:data/orig.js`）

## 環境メモ

- Windows。PowerShellはBOM問題があるため、日本語を含むファイルの書き込みは
  PowerShellの `Set-Content` ではなく Write ツールか Python を使うこと
- Python は `python`、Node は `node` で動く。`$env:PYTHONIOENCODING="utf-8"` を付けないと文字化けする
