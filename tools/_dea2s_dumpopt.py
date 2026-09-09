# -*- coding: utf-8 -*-
"""問題文＋選択肢テキストだけを出す（解説は出さない）"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
idx = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "DEA-C01_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")): idx[q["id"]] = q
for i in sys.argv[1:]:
    q = idx[i]
    print("=== %s [%s] nc=%d" % (i, q["domain"], q["n_correct"]))
    print("Q: %s" % q["question"])
    for o in q["options"]:
        print(" %s%s(%d) %s" % (o["letter"], "*" if o["correct"] else " ", len(o["text"]), o["text"]))
    print()
