# -*- coding: utf-8 -*-
"""複文率調整用ダンプ: python tools/_fukubun_dump.py EXAM [id...] [--two] [--zero] [--expl]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fukubun_lib import load, sent, overlap

exam = sys.argv[1]
args = [a for a in sys.argv[2:] if not a.startswith("--")]
flags = {a for a in sys.argv[2:] if a.startswith("--")}
_, index = load(exam)
ids = args
if "--two" in flags:
    ids = [i for i, (f, q) in index.items() if any(len(sent(o["text"])) >= 2 for o in q["options"])]
if "--zero" in flags:
    ids = [i for i, (f, q) in index.items() if not any(len(sent(o["text"])) >= 2 for o in q["options"])]
for i in sorted(ids):
    f, q = index[i]
    n2 = sum(1 for o in q["options"] if len(sent(o["text"])) >= 2)
    print("=== %s [%s/%s] n_correct=%d 肢%d 2文%d 重なり%.3f" % (
        i, q["domain"], q["level"], q["n_correct"], len(q["options"]), n2, overlap(q)))
    print("Q: %s" % q["question"])
    for o in q["options"]:
        print(" %s%s (%d字/%d文) %s" % (o["letter"], "*" if o["correct"] else " ",
              len(o["text"]), len(sent(o["text"])), o["text"]))
        if "--expl" in flags:
            print("      解説: %s" % (o.get("explanation") or ""))
    print()
