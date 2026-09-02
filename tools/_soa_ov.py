# -*- coding: utf-8 -*-
"""SOA-C03 の肢どうしの語の重なりを測る。対象30問と全体を出す。"""
import glob, json, re, statistics, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def overlap(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    if len(s) < 2: return None
    ps = [len(s[i] & s[j]) / len(s[i] | s[j]) for i in range(len(s)) for j in range(i+1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None
d = sys.argv[1] if len(sys.argv) > 1 else str(BASE / "資料" / "生成")
tg = set(json.load(open(BASE / "資料/生成/_overlap_target3_SOA-C03.json", encoding="utf-8")))
allv, tv = [], {}
for f in sorted(glob.glob(str(Path(d) / "*_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") != "SOA-C03" or q.get("set") != "orig" or not q.get("options"): continue
        v = overlap(q)
        if v is None: continue
        allv.append(v)
        if q["id"] in tg: tv[q["id"]] = v
for k in sorted(tv): print(f"  {k} {tv[k]:.3f}")
print(f"対象30問: 平均 {statistics.mean(tv.values()):.3f} ({len(tv)}問)")
print(f"SOA-C03 全体: 平均 {statistics.mean(allv):.3f} ({len(allv)}問)  公式 0.257")
