# -*- coding: utf-8 -*-
"""O-3(>=0.72)に該当する問題を、書き換え候補の肢つきで出力する。
使い方: python tools/_o3b_dump.py CLF-C02 [開始] [件数]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import load_mine, pairs, maxsim, overlap

exam = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
cnt = int(sys.argv[3]) if len(sys.argv) > 3 else 999
qs = [q for q in load_mine(exam) if q.get("type", "choice") == "choice" and q.get("options")]
hit = [q for q in qs if maxsim(q) >= 0.72 and not q.get("_ro")]
hit.sort(key=lambda q: -maxsim(q))
print("# %s O-3該当 %d問 / 全%d問 (%.1f%%)" % (exam, len(hit), len(qs), 100.0 * len(hit) / len(qs)))
for q in hit[start:start + cnt]:
    p = pairs(q)
    print("\n===== %s  最大%.3f  重なり%.3f  [%s]" % (q["id"], p[0][0], overlap(q), q["_file"]))
    print("Q: %s" % q["question"])
    top = {}
    for sim, wl, cl in p:
        top.setdefault(wl, sim)
    for o in q["options"]:
        mark = "○" if o.get("correct") else "  "
        s = "" if o.get("correct") else " (最大類似 %.3f)" % top.get(o["letter"], 0)
        print("%s %s: %s%s" % (mark, o["letter"], o["text"], s))
        print("      解説: %s" % (o.get("explanation") or "")[:160])
