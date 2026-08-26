# -*- coding: utf-8 -*-
"""同梱オリジナル問題データ(data/orig.js)のビルド

入力:
- 資料/生成/*_orig.json          … 新規生成したオリジナル問題(アプリ標準スキーマ)
- genai_dev_pro/quiz/questions.json … AIP-C01の既存オリジナル221問(旧quiz.pyスキーマ)を変換

出力: data/orig.js (window.ORIG_QUESTIONS = [...])
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN_DIR = BASE / "資料" / "生成"
AIP_LEGACY = Path(r"C:\Users\na7sh\Works\95_work\aws\06_lessons\genai_dev_pro\quiz\questions.json")
OUT = BASE / "data" / "orig.js"

AIP_DOMAINS = {
    "D1": "基盤モデル統合・データ管理・コンプライアンス",
    "D2": "実装と統合",
    "D3": "AI安全性・セキュリティ・ガバナンス",
    "D4": "運用効率と最適化",
    "D5": "テスト・検証・トラブルシューティング",
}


def convert_aip_legacy():
    if not AIP_LEGACY.exists():
        print("WARN: AIP既存問題ファイルなし、スキップ")
        return []
    data = json.load(open(AIP_LEGACY, encoding="utf-8"))
    out = []
    for i, q in enumerate(data["questions"], start=1):
        answers = [a.strip() for a in q["answer"].split(",")]
        options = []
        for letter in sorted(q["choices"].keys()):
            options.append({
                "letter": letter,
                "text": q["choices"][letter],
                "correct": letter in answers,
                "explanation": "",
            })
        out.append({
            "id": f"AIP-C01_orig_{i:03d}",
            "exam": "AIP-C01",
            "set": "orig",
            "type": "choice",
            "domain": AIP_DOMAINS.get(q.get("domain", ""), q.get("domain", "")),
            "level": q.get("level", ""),
            "question": q["question"],
            "n_correct": len(answers),
            "options": options,
            "explanation": q.get("explanation", ""),
        })
    return out


def load_generated():
    out = []
    if not GEN_DIR.exists():
        return out
    for f in sorted(GEN_DIR.glob("*_orig*.json")):
        try:
            qs = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"ERROR: {f.name}: {e}")
            continue
        ok = True
        for q in qs:
            n_marked = sum(1 for o in q["options"] if o["correct"])
            if n_marked != q["n_correct"] or n_marked == 0:
                print(f"ERROR: {f.name} {q['id']}: correct数不一致 ({n_marked} vs {q['n_correct']})")
                ok = False
            if not re.match(r"^[A-Z]{3}-C\d{2}_orig_\d+$", q["id"]):
                print(f"WARN: {f.name} {q['id']}: ID形式が非標準")
        if ok:
            out.extend(qs)
            print(f"OK: {f.name}: {len(qs)}問")
    return out


def main():
    questions = convert_aip_legacy() + load_generated()
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        sys.exit("ERROR: ID重複あり")
    js = "// 同梱オリジナル問題(自作)。公式問題はサイトに同梱せず、設定画面からローカル読み込みする(仕様書§3.8)\n"
    js += "window.ORIG_QUESTIONS = " + json.dumps(questions, ensure_ascii=False) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    from collections import Counter
    print("合計:", len(questions), dict(Counter(q["exam"] for q in questions)))


if __name__ == "__main__":
    main()
