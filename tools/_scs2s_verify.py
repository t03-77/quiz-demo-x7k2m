# -*- coding: utf-8 -*-
"""不変項目の照合。id/exam/set/type/domain/level/question/n_correct/letter/correct が不変か"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
snap = json.load(open(BASE / "tools" / "_scs2s_snapshot.json", encoding="utf-8"))
cur = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SCS-C03_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") == "SCS-C03": cur[q["id"]] = q
bad = []
if set(snap) != set(cur):
    bad.append("ID集合が変化: 消失%s 追加%s" % (sorted(set(snap)-set(cur))[:5], sorted(set(cur)-set(snap))[:5]))
for qid, s in snap.items():
    q = cur.get(qid)
    if not q: continue
    for k in ("exam", "set", "domain", "level", "n_correct", "question"):
        if q.get(k) != s[k]: bad.append("%s: %s が変化" % (qid, k))
    if q.get("type", "choice") != s["type"]: bad.append("%s: type が変化" % qid)
    so, qo = s["options"], q.get("options", [])
    if len(so) != len(qo):
        bad.append("%s: 選択肢数が変化 %d->%d" % (qid, len(so), len(qo))); continue
    for a, b in zip(so, qo):
        if a["letter"] != b["letter"]: bad.append("%s: letter が変化" % qid)
        if a["correct"] != b["correct"]: bad.append("%s[%s]: correct が変化" % (qid, a["letter"]))
    for o in qo:
        if not (o.get("explanation") or "").strip(): bad.append("%s[%s]: 解説が空" % (qid, o["letter"]))
        if not (o.get("text") or "").strip(): bad.append("%s[%s]: text が空" % (qid, o["letter"]))
print("照合 %d問 / 不一致 %d件" % (len(cur), len(bad)))
for b in bad[:30]: print("  " + b)
sys.exit(1 if bad else 0)
