# -*- coding: utf-8 -*-
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
ids = json.load(open(GEN / (sys.argv[3] if len(sys.argv)>3 else "_aip_short.json"), encoding="utf-8"))
idx = {}
for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    if not isinstance(d, list): continue
    for q in d:
        if isinstance(q, dict) and q.get("exam") == "AIP-C01":
            idx[q["id"]] = (Path(f).name, q)
sel = ids[int(sys.argv[1]):int(sys.argv[1])+int(sys.argv[2])]
for i in sel:
    f, q = idx[i]
    print(f"===== {i}  [{f}] domain={q['domain']} level={q.get('level')} n_correct={q['n_correct']} qlen={len(q['question'])}")
    print(f"Q: {q['question']}")
    for o in q["options"]:
        print(f"  {o['letter']} {'○' if o['correct'] else '×'} {o['text']}")
        print(f"     解説: {o.get('explanation','')}")
    print()
