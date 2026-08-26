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
| `tools/validate_questions.py` / `tools/smoke_test.js` | データ検証 |
| `資料/` | 元データ(解説集HTML、変換済みJSON、生成問題) ※gitignore対象にしてもよい |

## 問題データの二層構成(著作権対応・仕様書§3.8)

- **同梱セット** (`data/orig.js`): 自作のオリジナル問題。サイトに含めて配信してよい
- **ローカル読み込みセット** (`資料/変換済み/questions_all.json`): AWS公式問題1310問。サイトには含めず、アプリの「読み込む」ボタンからファイル選択で取り込む(IndexedDBに保存され端末内で完結)

## 開発メモ

- 詳細な仕様と進め方は `docs/仕様書.md` を参照
- オリジナル問題を追加するときは `資料/生成/{EXAM}_orig.json` に置いて `python tools/build_orig_data.py` を実行
- 公式問題バンクを更新するときは `資料/` の解説集HTMLを差し替えて `python tools/convert_kaisetsu_html.py` を実行
