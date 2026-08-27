# -*- coding: utf-8 -*-
"""パッチ案の「肢どうしの語の重なり」と長さを、適用前に見積もる。

使い方: python tools/_overlap_score.py <パッチ.json>
"""
import json
import re
import statistics
import sys
from collections import defaultdict

WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')


def ov(texts):
    s = [set(WORD.findall(t)) for t in texts]
    s = [x for x in s if x]
    if len(s) < 2:
        return None
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def main(path):
    per = defaultdict(dict)
    for p in json.load(open(path, encoding='utf-8')):
        per[p['id']][p['letter']] = p['text']
    vals, lens = [], []
    for qid in sorted(per):
        texts = [per[qid][k] for k in sorted(per[qid])]
        v = ov(texts)
        vals.append(v)
        L = [len(t) for t in texts]
        lens += L
        mark = '  ' if v >= 0.20 else 'NG'
        print(f'{mark} {qid} overlap={v:.3f} len={L}')
    print(f'-- {len(vals)}問 平均overlap={statistics.mean(vals):.3f} '
          f'中央={statistics.median(vals):.3f} 長さ中央={statistics.median(lens)}')


if __name__ == '__main__':
    main(sys.argv[1])
