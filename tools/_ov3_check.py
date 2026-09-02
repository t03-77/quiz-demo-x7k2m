# -*- coding: utf-8 -*-
"""パッチ適用前に、問題単位の重なり・長さ・解説字数を見積もる。"""
import json, glob, re, statistics, sys
from collections import defaultdict
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def ov(texts):
    s=[set(WORD.findall(t)) for t in texts]; s=[x for x in s if x]
    ps=[len(s[i]&s[j])/len(s[i]|s[j]) for i in range(len(s)) for j in range(i+1,len(s)) if s[i]|s[j]]
    return statistics.mean(ps) if ps else 0.0
idx={}
for f in sorted(glob.glob('資料/生成/*_orig*.json')):
    for q in json.load(open(f,encoding='utf-8')):
        if q.get('exam')=='DOP-C02': idx[q['id']]=q
per=defaultdict(dict); expl=defaultdict(dict)
for p in json.load(open(sys.argv[1],encoding='utf-8')):
    if 'text' in p: per[p['id']][p['letter']]=p['text']
    if 'expl' in p: expl[p['id']][p['letter']]=p['expl']
befs=[];afts=[];cl=0
for qid in sorted(per):
    q=idx[qid]
    before=[o['text'] for o in q['options']]
    after=[per[qid].get(o['letter'], o['text']) for o in q['options']]
    b,a=ov(before),ov(after)
    cor=[len(t) for t,o in zip(after,q['options']) if o['correct']]
    wr=[(o['letter'],len(t)) for t,o in zip(after,q['options']) if not o['correct']]
    cm=statistics.mean(cor)
    bad=[f"{L}:{n}" for L,n in wr if not (0.9*cm<=n<=1.1*cm)]
    longest = max(cor)>=max(n for _,n in wr)
    if longest: cl+=1
    el=[f"{L}:{len(e)}" for L,e in sorted(expl[qid].items()) if not (150<=len(e)<=250)]
    befs.append(b);afts.append(a)
    print(f"{qid} ov {b:.3f}->{a:.3f} 正解{cor} 誤答{[n for _,n in wr]} 平均{cm:.0f} "
          f"{'正解最長' if longest else ''} 範囲外[{','.join(bad)}] 解説外[{','.join(el)}]")
print(f"-- {len(befs)}問 平均 {statistics.mean(befs):.3f} -> {statistics.mean(afts):.3f}  正解最長 {cl}/{len(befs)}")
