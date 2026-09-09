# -*- coding: utf-8 -*-
import json, glob, sys, re
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:]]
full = "--full" in args
args = [a for a in args if a != "--full"]
ids = set(args)
idx = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SAP-C02_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        idx[q["id"]] = q
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
for i in sorted(ids):
    q = idx[i]
    print("=== %s  [%s/%s] n_correct=%d" % (i, q["domain"], q["level"], q["n_correct"]))
    print("Q(%d字): %s" % (len(q["question"]), q["question"]))
    for o in q["options"]:
        print(" %s%s (%d字/%d文) %s" % (o["letter"], "*" if o["correct"] else " ", len(o["text"]), len(sent(o["text"])), o["text"]))
        e = o.get("explanation") or ""
        if full:
            print("      解説(%d字): %s" % (len(e), e))
    print()
