# -*- coding: utf-8 -*-
"""書き換え候補の問題を丸ごと出力する。
使い方: python tools/_dvdo3_dump.py DVA-C02 id1 id2 ...
        python tools/_dvdo3_dump.py DVA-C02 --list        候補一覧
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1]
os.environ["O3EXAM"] = EX
import _dvdo3_lib as L
L.set_exam(EX)
qs = {q["id"]: q for q in L.load_mine()}
args = sys.argv[2:]
if args and args[0] == "--list":
    rows = []
    for q in L.load_mine():
        p = L.pairs(q)
        tw = [x for x in p if x[0] >= 0.72]
        if not tw:
            continue
        rest = [x for x in p if x[1] not in [t[1] for t in tw]]
        rows.append((q["id"], q["_file"].replace(EX + "_orig", ""), len(tw), p[0][0],
                     (rest[0][0] if rest else 0.0),
                     ",".join("%s(%.2f)" % (t[1], t[0]) for t in tw)))
    rows.sort(key=lambda r: (r[2], -r[3]))
    for r in rows:
        print("%-20s %-14s twins=%d max=%.2f rest=%.2f  %s" % r)
    print("計 %d問" % len(rows))
    sys.exit(0)
BRIEF = "--brief" in args
args = [a for a in args if not a.startswith("--")]
for qid in args:
    q = qs[qid]
    print("=" * 92)
    print("%s  [%s] domain=%s level=%s n_correct=%s" % (qid, q["_file"], q.get("domain"), q.get("level"), q.get("n_correct")))
    print("Q: " + q["question"])
    sim = {}
    for s, w, c in L.pairs(q):
        sim[w] = max(sim.get(w, 0), s)
    for o in q["options"]:
        mark = "◎正解" if o.get("correct") else "  誤答(sim=%.2f)" % sim.get(o["letter"], 0)
        print("  %s %s [%d字/%d文]" % (o["letter"], mark, len(o["text"]), len(L.sentences(o["text"]))))
        print("      text: " + o["text"])
        if not BRIEF:
            print("      exp : " + (o.get("explanation") or ""))
    print()
