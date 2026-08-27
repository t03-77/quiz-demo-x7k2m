# -*- coding: utf-8 -*-
"""担当3資格の「肢どうしの語の重なり」を 資料/生成/*_orig*.json から直接測る。"""
import json, glob, re, statistics, collections
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')
def ov(q):
    s=[set(WORD.findall(o.get('text',''))) for o in q.get('options',[]) if o.get('text')]
    s=[x for x in s if x]
    if len(s)<2: return None
    ps=[len(s[i]&s[j])/len(s[i]|s[j]) for i in range(len(s)) for j in range(i+1,len(s)) if s[i]|s[j]]
    return statistics.mean(ps) if ps else None
per=collections.defaultdict(list)
low={x['id'] for x in json.load(open(BASE/'資料/生成/_low_overlap.json',encoding='utf-8'))}
sub=collections.defaultdict(list)
for f in sorted(glob.glob(str(BASE/'資料/生成/*_orig*.json'))):
    for q in json.load(open(f,encoding='utf-8')):
        if q.get('set')!='orig' or q.get('type','choice')!='choice': continue
        v=ov(q)
        if v is None: continue
        per[q['exam']].append(v)
        if q['id'] in low: sub[q['exam']].append(v)
for ex in ['MLA-C01','DVA-C02','SOA-C03']:
    print(f"{ex} 全体 {statistics.mean(per[ex]):.3f} ({len(per[ex])}問) / 対象問題 {statistics.mean(sub[ex]):.3f} ({len(sub[ex])}問)")
