# -*- coding: utf-8 -*-
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
idx={}
for f in sorted(glob.glob(str(BASE/'資料'/'生成'/'DEA-C01_orig*.json'))):
    if '_bak' in f: continue
    for q in json.loads(Path(f).read_text(encoding='utf-8')):
        idx[q['id']]=q
tgt=json.loads((BASE/'資料'/'生成'/'_overlap_target3_DEA-C01.json').read_text(encoding='utf-8'))
for qid in tgt[int(sys.argv[1]):int(sys.argv[2])]:
    q=idx[qid]
    print('='*70)
    print(qid,'| n_correct',q['n_correct'],'|',q.get('domain'),'|',q.get('level'))
    print('Q:',q['question'])
    for o in q['options']:
        print(('  [O] ' if o['correct'] else '  [X] ')+o['letter']+'. ('+str(len(o['text']))+') '+o['text'])
