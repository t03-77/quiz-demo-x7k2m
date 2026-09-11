# -*- coding: utf-8 -*-
"""compact dump: 問題文(全文)＋肢テキストのみ。使い方: python tools/_sco3_c.py id1 id2 ..."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["O3EXAM"] = "SCS-C03"
import _sco3_lib as L
qs = {q["id"]: q for q in L.load_mine()}
for qid in sys.argv[1:]:
    q = qs[qid]
    sim = {}
    for s, w, c in L.pairs(q):
        sim[w] = max(sim.get(w, 0), s)
    print("### %s [%s] %s/%s n=%s" % (qid.replace("SCS-C03_orig_", ""), q["_file"].replace("SCS-C03_orig", "").replace(".json", "") or "0", q.get("domain"), q.get("level"), q.get("n_correct")))
    print("Q: " + q["question"])
    for o in q["options"]:
        print("  %s%s %s" % (o["letter"], "*" if o.get("correct") else ("%.2f" % sim.get(o["letter"], 0)), o["text"]))
    print()
