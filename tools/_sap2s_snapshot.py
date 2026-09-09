# -*- coding: utf-8 -*-
"""2文構造化作業の不変項目スナップショット（options[].text/explanation は変更可のため除外）"""
import json, glob
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "tools" / "_sap2s_snapshot.json"
EXAM = "SAP-C02"
snap = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SAP-C02_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") != EXAM: continue
        snap[q["id"]] = {"file": Path(f).name, "exam": q["exam"], "set": q.get("set"),
            "type": q.get("type", "choice"), "domain": q.get("domain"), "level": q.get("level"),
            "question": q["question"], "n_correct": q.get("n_correct"),
            "options": [{"letter": o["letter"], "correct": o["correct"], "text": o["text"]}
                        for o in q.get("options", [])]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %d問 -> %s" % (len(snap), OUT))
