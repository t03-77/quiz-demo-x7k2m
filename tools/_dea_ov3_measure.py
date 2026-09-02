# -*- coding: utf-8 -*-
import json, glob, re, statistics
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')
def ov(texts):
    s=[set(WORD.findall(t)) for t in texts]; s=[x for x in s if x]
    if len(s)<2: return None
    ps=[len(s[i]&s[j])/len(s[i]|s[j]) for i in range(len(s)) for j in range(i+1,len(s)) if s[i]|s[j]]
    return statistics.mean(ps) if ps else None
def collect(qs):
    r={}
    for q in qs:
        v=ov([o['text'] for o in (q.get('options') or [])])
        if v is not None: r[q['id']]=v
    return r
off=[q for q in json.loads((BASE/'資料'/'変換済み'/'questions_all.json').read_text(encoding='utf-8'))['questions'] if q.get('exam')=='DEA-C01']
mine=[]
for f in sorted(glob.glob(str(BASE/'資料'/'生成'/'*_orig*.json'))):
    if '_bak' in f: continue
    mine += [q for q in json.loads(Path(f).read_text(encoding='utf-8')) if q.get('exam')=='DEA-C01']
o=collect(off); m=collect(mine)
tgt=json.loads((BASE/'資料'/'生成'/'_overlap_target3_DEA-C01.json').read_text(encoding='utf-8'))
print('DEA-C01 公式 %d問 mean=%.3f' % (len(o), statistics.mean(o.values())))
print('DEA-C01 自作 %d問 mean=%.3f' % (len(m), statistics.mean(m.values())))
print('対象30問       mean=%.3f' % statistics.mean([m[i] for i in tgt if i in m]))
