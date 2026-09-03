# -*- coding: utf-8 -*-
import json, glob, sys, re
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
ids = set(sys.argv[1:])
full = "--full" in ids; ids.discard("--full")
idx = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SCS-C03_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")): idx[q["id"]] = q
for i in sorted(ids):
    q = idx[i]
    print("=== %s  [%s/%s] n_correct=%d" % (i, q["domain"], q["level"], q["n_correct"]))
    print("Q(%d字): %s" % (len(q["question"]), q["question"]))
    for o in q["options"]:
        print(" %s%s (%d字) %s" % (o["letter"], "*" if o["correct"] else " ", len(o["text"]), o["text"]))
        e = o.get("explanation") or ""
        print("      解説(%d字): %s" % (len(e), e if full else e[:150] + ("…" if len(e) > 150 else "")))
    print()
