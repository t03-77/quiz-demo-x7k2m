# -*- coding: utf-8 -*-
"""候補問題を簡潔に表示。O3EXAM=AIP-C01 python tools/_sao3_show.py 386 328 [--exp]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sao3_lib import load_mine, pairs, exam
EXP = "--exp" in sys.argv
ids = [a for a in sys.argv[1:] if not a.startswith("--")]
qs = {q["id"].split("_")[-1]: q for q in load_mine()}
for i in ids:
    q = qs[i]
    p = pairs(q)
    tgt = p[0][1]
    print("=" * 92)
    print("%s  %s  nc=%d  %s / %s   最類似=%s %.3f  2nd=%.3f"
          % (q["id"], q["_file"], q["n_correct"], q.get("domain"), q.get("level"),
             tgt, p[0][0], max([x[0] for x in p if x[1] != tgt] or [0])))
    print("Q:", q["question"])
    for o in q["options"]:
        mk = "*" if o.get("correct") else (">" if o["letter"] == tgt else " ")
        print(" %s[%s] (%d字) %s" % (mk, o["letter"], len(o["text"]), o["text"]))
        if EXP:
            print("      exp: %s" % (o.get("explanation") or ""))
