# -*- coding: utf-8 -*-
"""変換済みquestions_all.jsonの整合性チェック"""
import json
from collections import Counter
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "資料" / "変換済み" / "questions_all.json"
d = json.load(open(path, encoding="utf-8"))
qs = d["questions"]

print("total:", len(qs))
print("type:", dict(Counter(q["type"] for q in qs)))
print("needs_review:", [q["id"] for q in qs if q.get("needs_review")])
print("n_correct分布:", dict(Counter(q["n_correct"] for q in qs if q["type"] == "choice")))
print("セット別:", dict(Counter(f"{q['exam']}/{q['set']}" for q in qs)))

bad = []
for q in qs:
    if not q["question"].strip():
        bad.append((q["id"], "質問空"))
    if q["type"] == "choice":
        nc = sum(1 for o in q["options"] if o["correct"])
        if nc == 0 or nc != q["n_correct"]:
            bad.append((q["id"], "correct数", nc))
        if len(q["options"]) < 3:
            bad.append((q["id"], "options少", len(q["options"])))
        for o in q["options"]:
            if not o["explanation"].strip():
                bad.append((q["id"], f"解説空:{o['letter']}"))
            if not o["text"].strip():
                bad.append((q["id"], f"選択肢空:{o['letter']}"))
    elif q["type"] == "ordering":
        if len(q["order_answer"]) < 2:
            bad.append((q["id"], "order短", len(q["order_answer"])))
        if not q["explanation"].strip():
            bad.append((q["id"], "根拠空"))
    elif q["type"] == "matching":
        if not q["statements"] and not q.get("needs_review"):
            bad.append((q["id"], "statements空"))
        if not q["explanation"].strip():
            bad.append((q["id"], "根拠空"))

print("検証NG:", len(bad))
for b in bad[:20]:
    print("  ", b)
