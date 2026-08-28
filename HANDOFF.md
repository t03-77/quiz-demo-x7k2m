# 引き継ぎメモ（2026-08-27 時点）

別のAI・別の担当者が続きを行うための現状整理。

> **先に `CLAUDE.md` を読むこと。** 問題を作る・直すときの決まり（鉄則7つ）と、
> これまで実際に踏んだ失敗が書いてある。同じ失敗を繰り返さないために必要。
>
> 仕様は `docs/仕様書.md`。特に **§13「問題の品質基準」** が中核。

---

## このプロジェクトは何か

AWS認定資格の学習ウェブアプリ。静的HTML1枚（`index.html`）＋データファイル（`data/*.js`）で動く。
サーバー不要。`index.html` をブラウザで開けば使える。

公開先: https://t03-77.github.io/quiz-demo-x7k2m/
（`git push origin main` で反映。認証は保存済み）

**利用者の目的は「試験に合格すること」。** 本番より易しい問題は、どれだけ数を揃えても価値がない。
この一点がすべての判断基準になる。

---

## データの二層構成（重要・著作権対応）

| 種別 | 場所 | サイトに同梱 |
|---|---|---|
| オリジナル問題 1432問（自作） | `data/orig.js` | **する** |
| AWS公式問題 1290問 | `資料/変換済み/questions_all.json` | **しない**（利用者が手元のファイルを読み込む方式） |
| 読み上げ音声（自作問題ぶん） | `audio/aip-c01-orig_*.mp3` | **する**（2026-08-28〜。著作権の制約がない） |
| 読み上げ音声（公式問題ぶん） | `audio/aip-c01_*.mp3` ほか | **しない** |

`資料/` は `.gitignore` 済み。**この方針は崩さないこと。**

`audio/` は**ファイル名で選り分けている**。`audio/*` で全部除外したうえで、
`!audio/*-orig_*.mp3` だけを例外にしてある（`audio/` とディレクトリごと除外すると
中を探索しないため例外が効かない）。**新しく音声を作るときは命名規則に従うこと。**
自作問題ぶんは `-orig_` を必ず入れ、公式問題ぶんには入れない。

**公式問題を改変したものをサイトに載せてはいけない**（翻案にあたる）。
論点を参考にして別のシナリオで作るのは問題ない（アイデアは著作権の保護対象外）。

---

## 現在の到達状況

### できていること

| 項目 | 状態 |
|---|---|
| 問題数 | **1432問**（全11資格。各100〜121問） |
| 出題の形 | 1正解4肢 / 2正解5肢 / 3正解6肢 + マッチング15・並び替え15 |
| 問題文の分量 | 全11資格で公式模試の下位10%を下回る問題が **0問** |
| 解説の分量 | 全11資格が公式水準に到達 |
| ドメイン配分 | 全11資格が公式試験ガイドの比重と整合 |
| 当てやすさ | 「正解が最長」を9資格で公式並みに（例: DOP-C02 99%→17%） |
| 正解の位置 | データ上はAに82%偏るが、**出題時はシャッフルで A23/B22/C22/D25** |
| 事実の正確性 | 書き換えた誤答2271個のうち、裏取りが要る327件を検証し誤りは1件のみ |
| 機能 | 演習・模擬試験・SRS・弱点分析・図解・用語集・音声・AI連携・PWA・デモモード |
| テスト | E2E 17本すべて合格 |

### できていないこと（品質差の実測）

**ここが最重要。** 公式1047問と自作1181問を機械的に比較した結果。

| 指標 | 公式 | 自作 | 意味 |
|---|---|---|---|
| 正解と1点だけ違う誤答がある | 30.2% | **5.2%** | 細部を知らなくても大まかな理解で解ける |
| 2×2マトリクス構造 | 14.6% | **0.4%** | 2つの知識を両方持たないと解けない形が少ない |
| 「自前実装/手動」が正解になる | 11.8% | **0.8%** | **「手動と書いてあれば誤答」で解けてしまう** |
| 設定断片（JSON/ログ）を提示 | 5% | **0%** | 設定を読んで判断する問題がない |

出典を伏せた第三者判定でも、**消去法で解ける割合が公式46%に対し自作83%**。
改善前は89%だったので前進はしているが、まだ差がある。

---

## 残作業（優先度順）

### 0. 誤答肢の書き直し（**完了・2026-08-29**）

> **この作業は終わっている。再開する必要はない。**
> DVA-C02 48問すべてを書き直し、最長の肢が正解である割合を公式の分布に合わせた。
>
> | | 公式 | 現在 |
> |---|---|---|
> | DVA-C02 最長が正解 | 23.5% | **20.6%** |
> | DVA-C02 最長が誤答 | 74.1% | **72.5%** |
> | MLA-C01 最長が正解 | 21.0% | **26.0%** |
> | MLA-C01 最長が誤答 | 73.9% | **71.2%** |
>
> `audit_all.py` の「当てやすさ」もOKになっている。
>
> **MLA-C01 に残る24問は直してはいけない。** 「正解が最長」の問題数だけ見ると
> まだ24問あるが、分布で見ると既に公式並みで、直すと逆に振れる。
> 一度 DVA-C02 でこの失敗をしている（下記）。

以下は手順の記録（他の資格で同じ症状が出たときに使う）。

**やり方が確立したので、まずこれを続けるのが効率的。**

短い誤答を、正解と要素を共有した切りにくい誤答に置き換える。**正解肢は触らない。**
短い誤答は同時に質も低い（「手動で突き合わせ」「問題文が否定済みの方法」など、
中身を知らなくても切れるもの）ため、長さを揃えることが質を上げることと一致する。

手順:
1. `python -X utf8 tools/audit_difficulty.py` で「正解が最長」が公式より高い資格を選ぶ
2. 対象問題を抽出（下のコマンド）
3. パッチJSONを書く → `python tools/{資格}_apply_patch.py <patch> --dry` で長さを確認
   - **各問で誤答を1つは正解より長くする**。同値でも「正解が最長」の判定に引っかかる
4. 適用 → `build_orig_data.py` → `smoke_test.js` と `audit_consistency.py`
5. 10問ごとにコミット

```
python -X utf8 -c "
import json
js=open('data/orig.js',encoding='utf-8').read(); n=json.loads(js[js.index('['):js.rindex(']')+1])
for ex in ['DVA-C02','MLA-C01']:
    qs=[q for q in n if q.get('exam')==ex and q.get('set')=='orig' and q.get('options')]
    hit=[q['id'] for q in qs if min(len(o['text']) for o in q['options'] if o['correct']) > max(len(o['text']) for o in q['options'] if not o['correct'])]
    print(ex, len(hit), '問'); json.dump(hit, open('資料/生成/_longest_%s.json'%ex,'w'), ensure_ascii=False)
"
```

**やりすぎに注意。** 下げれば下げるほど良いわけではない。
DVA-C02 で 58%→11% まで下げたところ、最長の肢が正解である割合が 4.9% になり、
公式 23.5% を大きく下回った。「一番長い肢を捨てれば当たる」という逆の手がかりになる。
公式の値に**合わせる**こと。測り方は CLAUDE.md 鉄則4を参照。

> **2文以上（40% vs 23%）はこの作業では増えない。** 公式で多いのは
> 正解肢自体が「操作A。操作B。」の2文構造だから。誤答だけ直しても動かないことを
> 実測で確認済み（`資料/生成/_予測_長さと構造_2026-08-28.md`）。
> 着手するなら鉄則3の手順で正解肢を含めて組み直すこと。

### 1. O-3: 正解と1点だけ違う誤答を増やす（5.2% → 30%）

**難易度に最も効く。** 公式は正解とほぼ同文で1点だけ違う誤答を隣に置く。

> 正解「**行**レベルのフィルターでカナダの行へのアクセスを禁止」
> 誤答「**列**レベルのフィルターでカナダの行へのアクセスを禁止」

自作は誤答が「別の案」になっているため、大まかな理解で正解にたどり着ける。

対象の抽出:
```
python -X utf8 -c "
import json
from difflib import SequenceMatcher
js=open('data/orig.js',encoding='utf-8').read(); n=json.loads(js[js.index('['):js.rindex(']')+1])
out=[]
for q in n:
    if q.get('set')!='orig' or not q.get('options'): continue
    cor=[o['text'] for o in q['options'] if o.get('correct')]
    wrong=[o['text'] for o in q['options'] if not o.get('correct')]
    if not cor or not wrong: continue
    if max(SequenceMatcher(None,c,w).ratio() for c in cor for w in wrong) < 0.72:
        out.append(q['id'])
print(len(out)); json.dump(out, open('資料/生成/_need_nearmiss.json','w'), ensure_ascii=False)
"
```

### 2. W-6: 「手動＝誤答」のメタ規則を解消

公式では「自分でLambdaを書く」「手動で対応する」が**正解になることが11.8%ある**
（例: DOP-C02_exam_013 の正解は「Lambdaを自作してRun Commandを呼ぶ」）。
自作は0.8%しかないため、中身を知らなくても切れる抜け道になっている。

### 3. AIP-C01の「1正解5肢」80問を4肢にする

公式1070問に「1正解5肢」は**1問もない**。他5資格の86問は修正済みで、AIP-C01だけ残っている。
手順は `tools/apply_5opt_trim.py` と `資料/生成/_5opt_delete_map.json` を参照。

### 4. 論点の洗い出しを他資格へ展開

AIP-C01で実施済み。**公式95問を全問読んだところ、自作106問がカバーする論点は実質74件で、
55件が未カバー、しかも上位21論点に53問（50%）が集中**していた。

```
資料/生成/_topics_AIP-C01.json      公式95問の論点一覧
資料/生成/_topic_gap_AIP-C01.md     公式にあって自作にない論点
```

残り10資格。1資格あたり1.5〜3時間（公式問題数に比例）、合計20〜24時間相当の見込み。
公式問題数: AIF/CLF/DEA/MLA/SOA が150問、DOP/SAP が95問、SAA/DVA/SCS が85問。

### 5. その他

- AIP-C01以外の読み上げ音声（1資格あたり3〜4時間）
- AI機能を実際のAPIキーで未検証（テストはすべて模擬応答）
- ローカル専用のAPIキー設定（デモ時に本物の応答を見せたい場合）

---

## 作業の手順

### 問題を作る・直す前に

1. `CLAUDE.md` を読む
2. `資料/作問ガイド/{EXAM}.md` を読む（なければ `python tools/make_exam_guide.py {EXAM}`）
3. `資料/生成/_review_criteria_v2.md`（58項目のチェックリスト）を読む

### 直したあとに必ず

```
python tools/build_orig_data.py      # 資料/生成/*.json → data/orig.js
python tools/audit_all.py            # 全観点を一括実行
python tools/audit_criteria.py       # チェックリスト58項目の充足状況
```

個別の検査:

| コマンド | 見るもの |
|---|---|
| `node tools/smoke_test.js` | ID重複・スキーマ |
| `python tools/audit_consistency.py` | 解説と正誤フラグの矛盾 |
| `python tools/audit_domains.py` | ドメイン配分 |
| `python tools/audit_explanations.py` | 解説の分量 |
| `python tools/audit_difficulty.py` | 当てやすさ |
| `python tools/audit_content.py` | 重複・出題の形・古い情報・偏り |

### E2Eテスト（17本）

```
cd %TEMP% && mkdir quizapp_e2e && cd quizapp_e2e
npm init -y && npm i playwright-core
copy <プロジェクト>\tests\* .
node test.js
```

`chromium.launch({channel:'msedge'})` で動く（ブラウザの別途インストール不要）。

**`answer.js` が共通ヘルパー。** 出題はマッチング・並び替え・複数選択も混ざるため、
`.opt` を1つクリックする前提のテストは失敗する。必ず次を使うこと:
- `waitQuestion(page)` … 形式を問わず問題の表示を待つ
- `answer(page, correct)` … 形式を問わず回答して採点画面まで
- `choose(page)` … 回答だけ（模試は途中で採点画面を出さない）
- `startChoiceQuestion(page)` … 選択式限定の機能を試すとき

---

## ファイル構成

```
index.html                     アプリ本体（1枚で完結）
sw.js / manifest.webmanifest   PWA
data/
  exams.js                     試験マスタ（問題数・時間・合格スコア）
  orig.js                      同梱するオリジナル問題（ビルド生成物・直接編集しない）
  glossary.js                  用語集260語
  diagrams.js                  図解14種（Mermaid）
  audio_tracks*.js             音声トラック定義
docs/仕様書.md                  仕様（§13が品質基準）
CLAUDE.md                      作業の決まり（鉄則7つ）
tools/                         ビルド・検査・生成スクリプト
tests/                         E2Eテスト17本
資料/                           .gitignore対象
  変換済み/questions_all.json    公式1290問（比較の基準）
  生成/*.json                    問題のソース（ここを編集してビルドする）
  作問ガイド/{EXAM}.md            公式全問から作った基準
  生成/_review_criteria_v2.md    チェックリスト58項目
```

---

## 環境メモ

- Windows。**日本語を含むファイルの書き込みに PowerShell の `Set-Content` を使わない**（文字化けする）
- PowerShellのヒアドキュメント内でPythonコードを書くと引用符で壊れやすい。複雑な置換はエディタで行う
- Python は `python`、Node は `node`。`$env:PYTHONIOENCODING="utf-8"` を付けないと文字化けする
- `python ... | Select-Object -First 3` のように出力を絞ると、それ以上出力した時点でプロセスが落ちる
