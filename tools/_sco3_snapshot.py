# -*- coding: utf-8 -*-
"""O-3是正作業の不変項目スナップショット（SCS-C03）。
鉄則3: id/exam/set/type/domain/level/question/n_correct/letter/correct は不変。
本作業では「正解肢の text も触らない」ため、正解肢 text も保存して照合する。
使い方: python tools/_sco3_snapshot.py SCS-C03
"""
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("O3EXAM", "SCS-C03")
os.environ["O3EXAM"] = EX
import _sco3_lib as L
L.set_exam(EX)
OUT = Path(__file__).resolve().parent / ("_sco3_snapshot_%s.json" % EX)
snap = {}
for q in L.load_mine():
    snap[q["id"]] = {"file": q["_file"], "exam": q["exam"], "set": q.get("set"),
        "type": q.get("type", "choice"), "domain": q.get("domain"), "level": q.get("level"),
        "question": q["question"], "n_correct": q.get("n_correct"),
        "options": [{"letter": o["letter"], "correct": o["correct"],
                     "correct_text": o["text"] if o.get("correct") else None}
                    for o in q.get("options", [])]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %s %d問 -> %s" % (EX, len(snap), OUT.name))
