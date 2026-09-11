# -*- coding: utf-8 -*-
"""不変項目の照合（正解肢 text を含む）。使い方: python tools/_sco3_verify.py SCS-C03"""
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("O3EXAM", "SCS-C03")
os.environ["O3EXAM"] = EX
import _sco3_lib as L
L.set_exam(EX)
snap = json.load(open(Path(__file__).resolve().parent / ("_sco3_snapshot_%s.json" % EX), encoding="utf-8"))
cur = {q["id"]: q for q in L.load_mine()}
bad = []
if set(snap) != set(cur):
    bad.append("ID集合が変化: 消失%s 追加%s" % (sorted(set(snap) - set(cur))[:5], sorted(set(cur) - set(snap))[:5]))
for qid, s in snap.items():
    q = cur.get(qid)
    if not q:
        continue
    if q["_file"] != s["file"]:
        bad.append("%s: 所属ファイルが変化" % qid)
    for k in ("exam", "set", "domain", "level", "n_correct", "question"):
        if q.get(k) != s[k]:
            bad.append("%s: %s が変化" % (qid, k))
    if q.get("type", "choice") != s["type"]:
        bad.append("%s: type が変化" % qid)
    so, qo = s["options"], q.get("options", [])
    if len(so) != len(qo):
        bad.append("%s: 選択肢数が変化 %d->%d" % (qid, len(so), len(qo)))
        continue
    for a, b in zip(so, qo):
        if a["letter"] != b["letter"]:
            bad.append("%s: letter が変化 %s->%s" % (qid, a["letter"], b["letter"]))
        if a["correct"] != b["correct"]:
            bad.append("%s[%s]: correct が変化" % (qid, a["letter"]))
        if a["correct"] and a["correct_text"] != b["text"]:
            bad.append("%s[%s]: **正解肢の text が変化**" % (qid, a["letter"]))
    for o in qo:
        if not (o.get("explanation") or "").strip():
            bad.append("%s[%s]: 解説が空" % (qid, o["letter"]))
        if not (o.get("text") or "").strip():
            bad.append("%s[%s]: text が空" % (qid, o["letter"]))
print("[%s] 照合 %d問 / 不一致 %d件" % (EX, len(cur), len(bad)))
for b in bad[:30]:
    print("  " + b)
sys.exit(1 if bad else 0)
