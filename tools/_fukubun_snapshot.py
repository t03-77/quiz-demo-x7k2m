# -*- coding: utf-8 -*-
"""複文率調整の不変項目スナップショット(SAA-C03/AIF-C01)"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fukubun_lib import load, BASE

OUT = BASE / "tools" / "_fukubun_snapshot.json"
snap = {}
for exam in ("SAA-C03", "AIF-C01"):
    _, index = load(exam)
    for qid, (f, q) in index.items():
        snap[qid] = {"file": Path(f).name, "exam": q["exam"], "set": q.get("set"),
                     "type": q.get("type", "choice"), "domain": q.get("domain"),
                     "level": q.get("level"), "question": q["question"],
                     "n_correct": q.get("n_correct"),
                     "options": [{"letter": o["letter"], "correct": o["correct"]} for o in q["options"]]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %d問 -> %s" % (len(snap), OUT))
