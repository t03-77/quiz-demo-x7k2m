# -*- coding: utf-8 -*-
"""DVA-C02 2文構造化作業の不変項目スナップショット。
正解肢の text は変更可なので保存しないが、correct フラグと旧 text の技術トークンは保存する。"""
import json, glob, re
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "tools" / "_dva2s_snapshot.json"
EXAM = "DVA-C02"
TOK = re.compile(r"[A-Za-z][A-Za-z0-9_:\-]*|[ァ-ヶー]{3,}|[一-龥]{2,}|[0-9]+")
snap = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / (EXAM + "_orig*.json")))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") != EXAM:
            continue
        snap[q["id"]] = {
            "file": Path(f).name, "exam": q["exam"], "set": q.get("set"),
            "type": q.get("type", "choice"), "domain": q.get("domain"), "level": q.get("level"),
            "question": q["question"], "n_correct": q.get("n_correct"),
            "options": [{"letter": o["letter"], "correct": o["correct"],
                         "text": o["text"],
                         "tokens": sorted(set(TOK.findall(o["text"])))} for o in q.get("options", [])]}
if OUT.exists():
    raise SystemExit("既にあります: %s" % OUT)
OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print("snapshot: %d問 -> %s" % (len(snap), OUT.name))
