# -*- coding: utf-8 -*-
"""模試キャリブレーション用に、公式模擬試験/Pretestから各試験3問のお手本を抽出する"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "資料" / "変換済み" / "questions_all.json"
OUT_DIR = BASE / "資料" / "校正サンプル"

d = json.load(open(SRC, encoding="utf-8"))
qs = [q for q in d["questions"] if q["set"] in ("exam", "pretest") and q["type"] == "choice"]

OUT_DIR.mkdir(exist_ok=True)
by_exam = {}
for q in qs:
    by_exam.setdefault(q["exam"], []).append(q)

for exam, items in by_exam.items():
    # 中盤の問題から、選択肢が4つ以上で問題文が長め(=シナリオ型)のものを3問
    cands = sorted(items, key=lambda q: -len(q["question"]))
    picks = cands[len(cands)//4 : len(cands)//4 + 3]
    lines = [f"# {exam} 公式問題のお手本(難易度・文体の基準)\n"]
    for q in picks:
        lines.append(f"## {q['id']}")
        lines.append(q["question"])
        for o in q["options"]:
            lines.append(f"{o['letter']}. {o['text']} {'[正解]' if o['correct'] else ''}")
        lines.append("")
    (OUT_DIR / f"{exam}.md").write_text("\n".join(lines), encoding="utf-8")
    print(exam, len(picks), "問")
