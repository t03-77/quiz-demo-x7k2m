# -*- coding: utf-8 -*-
"""軸そろえの追加対象を、選択肢テキストだけ短く出力する。
使い方: python tools/axis_dump2.py EXAM 件数 [開始]"""
import json, glob, re, statistics, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')
def ov(q):
    s=[set(WORD.findall(o.get('text',''))) for o in q.get('options',[]) if o.get('text')]
    s=[x for x in s if x]
    if len(s)<2: return 0.0
    ps=[len(s[i]&s[j])/len(s[i]|s[j]) for i in range(len(s)) for j in range(i+1,len(s)) if s[i]|s[j]]
    return statistics.mean(ps) if ps else 0.0
exam=sys.argv[1]; n=int(sys.argv[2]); start=int(sys.argv[3]) if len(sys.argv)>3 else 0
done=set()
for f in glob.glob(str(BASE/'資料/生成/_axis_*.json')):
    for p in json.load(open(f,encoding='utf-8')): done.add(p['id'])
rows=[]
for f in sorted(glob.glob(str(BASE/'資料/生成/*_orig*.json'))):
    for q in json.load(open(f,encoding='utf-8')):
        if q.get('exam')!=exam or q.get('set')!='orig' or q.get('type','choice')!='choice': continue
        if q['id'] in done: continue
        rows.append((ov(q), q))
rows.sort(key=lambda x:x[0])
for v,q in rows[start:start+n]:
    print('='*80)
    print(f"{q['id']} ov={v:.3f} n_correct={q.get('n_correct')} domain={q.get('domain')}")
    print('Q: '+q['question'])
    for o in q['options']:
        print(f"  {o['letter']}{'*' if o['correct'] else ' '} ({len(o['text'])}) {o['text']}")
