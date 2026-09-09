# -*- coding: utf-8 -*-
"""指定 id の問題を全文表示する。使い方: python tools/_o3b_show.py CLF-C02 003 046 ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import load_mine, pairs, overlap

exam = sys.argv[1]
want = set(sys.argv[2:])
idx = {q["id"]: q for q in load_mine(exam)}
for w in sys.argv[2:]:
    qid = w if w in idx else "%s_orig_%s" % (exam, w)
    q = idx.get(qid)
    if not q:
        print("!! 見つからない: %s" % w)
        continue
    p = pairs(q)
    top = {}
    for sim, wl, cl in p:
        top[wl] = max(top.get(wl, 0), sim)
    print("\n===== %s  max=%.3f ov=%.3f n_correct=%s domain=%s level=%s [%s]"
          % (q["id"], p[0][0], overlap(q), q.get("n_correct"), q.get("domain"), q.get("level"), q["_file"]))
    print("Q: %s" % q["question"])
    for o in q["options"]:
        mark = "*" if o.get("correct") else " "
        s = "" if o.get("correct") else "  [%.3f]" % top.get(o["letter"], 0)
        print("%s%s(%d字): %s%s" % (mark, o["letter"], len(o["text"]), o["text"], s))
        print("     解説(%d字): %s" % (len(o.get("explanation") or ""), o.get("explanation") or ""))
