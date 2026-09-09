# -*- coding: utf-8 -*-
"""コンパクト表示: 問題文＋全肢のtext（解説は書換対象肢のみ）"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _saao3_lib import load_mine, pairs, overlap, WORD
idx = {q["id"]: q for q in load_mine()}
for a in sys.argv[1:]:
    qid, tgt = a.split(":") if ":" in a else (a, None)
    q = idx["SAA-C03_orig_%s" % qid]
    ps = {}
    for s, w, c in pairs(q):
        ps[w] = max(ps.get(w, 0), s)
    print("=" * 88)
    print("%s [%s] ov=%.3f  書換対象=%s" % (q["id"], q["_file"], overlap(q), tgt))
    print("Q: " + q["question"])
    for o in q["options"]:
        m = "◎" if o.get("correct") else ("★" if o["letter"] == tgt else "・")
        print(" %s%s: %s%s" % (m, o["letter"], o["text"], "" if o.get("correct") else " [sim=%.3f]" % ps[o["letter"]]))
    # 他の誤答肢の語彙（重なりを守るために再利用する語）
    other = set()
    for o in q["options"]:
        if not o.get("correct") and o["letter"] != tgt:
            other |= set(WORD.findall(o["text"]))
    cor = set()
    for o in q["options"]:
        if o.get("correct"): cor |= set(WORD.findall(o["text"]))
    print("  他誤答の語: " + " ".join(sorted(other)))
    print("  他誤答のみ(正解に無い語): " + " ".join(sorted(other - cor)))
