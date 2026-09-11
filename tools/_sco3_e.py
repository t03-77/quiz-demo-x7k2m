# -*- coding: utf-8 -*-
"""対象肢の現在の text/explanation と、他肢の explanation 冒頭を出す。
使い方: python tools/_sco3_e.py 006:D 011:B ..."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["O3EXAM"] = "SCS-C03"
import _sco3_lib as L
qs = {q["id"]: q for q in L.load_mine()}
for a in sys.argv[1:]:
    num, lets = a.split(":")
    q = qs["SCS-C03_orig_" + num]
    print("### %s" % num)
    for o in q["options"]:
        tag = "*" if o.get("correct") else " "
        if o["letter"] in lets:
            print("  [TARGET] %s%s text: %s" % (o["letter"], tag, o["text"]))
            print("           exp : %s" % (o.get("explanation") or ""))
        else:
            print("  %s%s exp: %s" % (o["letter"], tag, (o.get("explanation") or "")))
    print()
