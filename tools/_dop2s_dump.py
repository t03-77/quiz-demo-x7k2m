# -*- coding: utf-8 -*-
import json, glob, sys, re
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
full = "--full" in sys.argv
idx = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "DOP-C02_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") == "DOP-C02": idx[q["id"]] = q
for i in args:
    q = idx[i]
    print("=== %s  [%s/%s] n_correct=%d" % (i, q["domain"], q["level"], q["n_correct"]))
    print("Q: %s" % q["question"])
    for o in q["options"]:
        n = len(sent(o["text"]))
        print(" %s%s <%d文/%d字> %s" % (o["letter"], "*" if o["correct"] else " ", n, len(o["text"]), o["text"]))
        if full:
            print("      解説: %s" % (o.get("explanation") or ""))
    print()
