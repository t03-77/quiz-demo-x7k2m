# -*- coding: utf-8 -*-
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _twin_measure import load, maxsim
from difflib import SequenceMatcher

ids = sys.argv[1:]
qs = {q["id"]: q for q in load()}
for i in ids:
    q = qs[i]
    cor = [o["text"] for o in q["options"] if o.get("correct")]
    print("=" * 90)
    print(f'{q["id"]}  [{q["_file"]}] domain={q["domain"]} level={q["level"]} n_correct={q.get("n_correct")}')
    print("Q: " + q["question"])
    for o in q["options"]:
        s = max(SequenceMatcher(None, c, o["text"]).ratio() for c in cor) if not o.get("correct") else 1.0
        print(f'  [{o["letter"]}] {"O" if o.get("correct") else "x"} sim={s:.3f} len={len(o["text"])}')
        print(f'      T: {o["text"]}')
        print(f'      E: {o.get("explanation","")}')
