# -*- coding: utf-8 -*-
import json, glob, re, statistics, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')
def ov(t):
    s=[set(WORD.findall(x)) for x in t]; s=[x for x in s if x]
    ps=[len(s[i]&s[j])/len(s[i]|s[j]) for i in range(len(s)) for j in range(i+1,len(s)) if s[i]|s[j]]
    return statistics.mean(ps) if ps else 0
idx={}
for f in sorted(glob.glob(str(BASE/'資料'/'生成'/'DEA-C01_orig*.json'))):
    if '_bak' in f: continue
    for q in json.loads(Path(f).read_text(encoding='utf-8')):
        idx[q['id']]=q
ids=sys.argv[1:]
if ids==['ALL']:
    ids=json.loads((BASE/'資料'/'生成'/'_overlap_target3_DEA-C01.json').read_text(encoding='utf-8'))
vals=[]; nlong=0
for qid in ids:
    q=idx[qid]; op=q['options']
    cor=[o for o in op if o['correct']]; wr=[o for o in op if not o['correct']]
    cmean=statistics.mean(len(o['text']) for o in cor)
    lo,hi=cmean*0.9,cmean*1.1
    ngs=[f"{o['letter']}:{len(o['text'])}" for o in wr if not lo<=len(o['text'])<=hi]
    exl=[f"{o['letter']}:{len(o['explanation'] or '')}" for o in wr
         if not 150<=len(o['explanation'] or '')<=250]
    long_ = max(len(o['text']) for o in cor)>max(len(o['text']) for o in wr)
    nlong += long_
    v=ov([o['text'] for o in op]); vals.append(v)
    print(f"{qid} ov={v:.3f} 正解平均{cmean:.0f} "
          f"[{' '.join(str(len(o['text'])) for o in op)}] {'正解が最長' if long_ else ''}"
          + (f"  LEN_NG {','.join(ngs)}" if ngs else "")
          + (f"  EXPL_NG {','.join(exl)}" if exl else ""))
print(f"-- {len(vals)}問 mean overlap={statistics.mean(vals):.3f} / 正解が最長 {nlong}問")
