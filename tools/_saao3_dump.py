# -*- coding: utf-8 -*-
"""指定idの問題を全文表示（O-3是正の下書き用）"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saao3_lib import load_mine, pairs, overlap
ids = sys.argv[1:]
idx = {q["id"]: q for q in load_mine()}
for i in ids:
    q = idx["SAA-C03_orig_%s" % i] if not i.startswith("SAA") else idx[i]
    ps = {(w, c): s for s, w, c in pairs(q)}
    print("=" * 90)
    print("%s  [%s] domain=%s level=%s n_correct=%s ov=%.3f" % (q["id"], q["_file"], q.get("domain"), q.get("level"), q.get("n_correct"), overlap(q)))
    print("Q: " + q["question"])
    for o in q["options"]:
        mark = "◎正" if o.get("correct") else "  誤"
        sim = "" if o.get("correct") else "  sim=%.3f" % max(v for (w, c), v in ps.items() if w == o["letter"])
        print(" %s %s: %s%s" % (mark, o["letter"], o["text"], sim))
        print("      解説: %s" % (o.get("explanation") or "")[:200])
