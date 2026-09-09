# -*- coding: utf-8 -*-
"""O-3是正作業の不変項目スナップショット(CLF-C02 / SOA-C03)。
鉄則3: id/exam/set/type/domain/level/question/n_correct/letter/correct は不変。
本作業では「正解肢の text も触らない」ため、正解肢 text も保存して照合する。
使い方: python tools/_o3b_snapshot.py CLF-C02"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import load_mine
exam = sys.argv[1]
OUT = Path(__file__).resolve().parent / ("_o3b_snapshot_%s.json" % exam)
snap = {}
for q in load_mine(exam):
    snap[q["id"]] = {"file": q["_file"], "exam": q["exam"], "set": q.get("set"),
        "type": q.get("type", "choice"), "domain": q.get("domain"), "level": q.get("level"),
        "question": q["question"], "n_correct": q.get("n_correct"),
        "options": [{"letter": o["letter"], "correct": o["correct"],
                     "correct_text": o["text"] if o.get("correct") else None}
                    for o in q.get("options", [])]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %s %d問 -> %s" % (exam, len(snap), OUT.name))
