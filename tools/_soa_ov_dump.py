# -*- coding: utf-8 -*-
import glob, json, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
tg = json.load(open(BASE / "資料/生成/_overlap_target3_SOA-C03.json", encoding="utf-8"))
want = set(sys.argv[1:]) or set(tg)
idx = {}
for f in sorted(glob.glob(str(BASE / "資料/生成/*_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") == "SOA-C03": idx[q["id"]] = (Path(f).name, q)
for qid in tg:
    if qid not in want: continue
    fn, q = idx[qid]
    print(f"===== {qid}  [{fn}] domain={q.get('domain')} level={q.get('level')} n_correct={q.get('n_correct')}")
    print(f"Q({len(q['question'])}字): {q['question']}")
    for o in q["options"]:
        m = "正解" if o["correct"] else "誤答"
        print(f"  -- {o['letter']} [{m}] ({len(o['text'])}字) {o['text']}")
        print(f"     expl({len(o.get('explanation') or '')}字): {o.get('explanation')}")
    print()
