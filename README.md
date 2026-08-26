# cert_quiz_app

資格試験の学習ウェブアプリ(開発中)。AWS認定12資格に対応。

- 問題演習、正誤記録と正答率の可視化、読み上げ音声、用語解説、AI連携を予定
- サーバーを持たない静的サイト。学習の進捗は利用者のブラウザ内にのみ保存される
- 公開: GitHub Pages

## 構成

| パス | 内容 |
|---|---|
| `index.html` | アプリ本体 |
| `data/exams.js` | 試験マスタ(ここに追記すれば試験が増える) |
| `data/orig.js` | 同梱オリジナル問題(自作321問)。`tools/build_orig_data.py` で生成 |
| `data/glossary.js` | 用語辞書 |
| `data/demo_audio.js` | デモ音声(base64) |
| `docs/仕様書.md` | 機能仕様 |
| `tools/convert_kaisetsu_html.py` | 解説集HTML → 公式問題バンクJSON変換 |
| `tools/build_orig_data.py` | オリジナル問題(資料/生成/*.json + AIP既存221問) → data/orig.js |
| `tools/make_audio_vv.py` | 読み上げ音声の生成(VOICEVOX、チャプター付き) |
| `tools/survey_generated.py` | 生成問題の完成度と欠番を確認 |
| `tools/consolidate_fragments.py` | 生成が中断して残った断片ファイルを正規ファイルへ統合 |
| `tools/merge_explanation_chunks.py` | 解説の一括書き直しで各所に残った中間ファイルを本体へ安全に取り込む |
| `tools/make_calibration_samples.py` | 公式模試から**解説つき**のお手本を抽出(生成・書き直しの基準に使う) |
| `tools/audit_explanations.py` | 解説の分量を公式模試と比較(URL誘導を除いた実質字数で判定) |
| `tools/audit_domains.py` | ドメイン配分を公式試験ガイドの比重と突合 |
| `tools/audit_consistency.py` | 解説と正誤フラグの矛盾を検出 |
| `tools/audit_enumerations.py` | 「対応するのはA、B、C」型の列挙漏れ候補を洗い出す |
| `tools/audit_risky_claims.py` | 料金・SLA・数値上限など事実誤認になりやすい記述を洗い出す |
| `tools/audit_padding.py` | 解説が字数合わせの水増しになっていないかを検査 |
| `tools/review_quality.py` | 問題文・選択肢の長さや条件句の割合を公式と比較 |
| `tools/validate_questions.py` / `tools/smoke_test.js` | データ検証 |

## 問題の品質基準

公式模試を「お手本」として、次の水準に揃えている。基準は `資料/校正サンプル/{EXAM}.md`（公式問題を解説つきで抽出したもの）。

- **問題文**: 制約条件を含むシナリオ形式。「最もコスト効率が良い」等の選定条件を入れる
- **誤答選択肢**: 一見もっともらしく、決定的な理由で違うもの。明らかな捨て選択肢を作らない
- **解説**: 正解は仕組みレベルで「なぜ満たすか」、誤答は「どの条件で破綻するか」を述べる
- **ドメイン配分**: 公式試験ガイドの比重に沿わせる
- 変わりやすい数値上限・料金・リージョン対応状況は書かない

計測は `python tools/audit_explanations.py` と `python tools/audit_domains.py` で行う。
なお公式解説は字数の約半分がURL誘導のため、比較時はそれを除いた実質字数で見ること。

## 主な学習機能

- **出題の優先度**: 要復習 → 復習期 → 未出題 → 再確認待ち。2回連続正解で習得済み
- **間隔反復(SRS)**: 習得済みの問題を 1→3→7→14→30日 の間隔で自動再出題(不正解でリセット)
- **模擬試験モード**: 10/25/65問、タイマー付き、途中の正解表示なし、終了時に合格ライン(70%)と比較
- **分野別の正答率**: 弱点の分野をタップするとその分野だけ復習できる
- **選択肢シャッフル**: 記号の丸暗記を防ぐ(設定でON)
- **AI連携(任意)**: 問題へのAI質問、用語の深掘り、テキスト/画像からの問題追加。月次予算上限で自動停止
- **キーボード操作**: A〜Fで選択、Enterで回答・次へ
| `資料/` | 元データ(解説集HTML、変換済みJSON、生成問題) ※gitignore対象にしてもよい |

## 問題データの二層構成(著作権対応・仕様書§3.8)

- **同梱セット** (`data/orig.js`): 自作のオリジナル問題。サイトに含めて配信してよい
- **ローカル読み込みセット** (`資料/変換済み/questions_all.json`): AWS公式問題1310問。サイトには含めず、アプリの「読み込む」ボタンからファイル選択で取り込む(IndexedDBに保存され端末内で完結)

## 開発メモ

- 詳細な仕様と進め方は `docs/仕様書.md` を参照
- オリジナル問題を追加するときは `資料/生成/{EXAM}_orig.json` に置いて `python tools/build_orig_data.py` を実行
- 公式問題バンクを更新するときは `資料/` の解説集HTMLを差し替えて `python tools/convert_kaisetsu_html.py` を実行
