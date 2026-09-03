# -*- coding: utf-8 -*-
"""2文構造化作業の不変項目スナップショット（正解肢 text は変更可のため除外、correct フラグは保存）"""
import json, glob
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "tools" / "_scs2s_snapshot.json"
EXAM = "SCS-C03"
snap = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SCS-C03_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") != EXAM: continue
        snap[q["id"]] = {"file": Path(f).name, "exam": q["exam"], "set": q.get("set"),
            "type": q.get("type", "choice"), "domain": q.get("domain"), "level": q.get("level"),
            "question": q["question"], "n_correct": q.get("n_correct"),
            "options": [{"letter": o["letter"], "correct": o["correct"]} for o in q.get("options", [])]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %d問 -> %s" % (len(snap), OUT))
