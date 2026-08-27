"""v2レビュー用: サンプル100問を20問ずつ可読テキストに出力する一時スクリプト。"""
import json, io, os, sys, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(io.open(os.path.join(BASE, '資料', '生成', '_review_v2_sample.json'), encoding='utf-8'))
qs = d['questions']
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else 230


def clean(s):
    s = re.sub(r'\s*\n\s*', ' ', (s or '').strip())
    s = re.sub(r'詳細については、.*$', '', s)
    s = re.sub(r'に関するページを参照してください。?', '', s)
    return s.strip()


for b in range(5):
    lines = []
    for q in qs[b * 20:(b + 1) * 20]:
        lines.append('=' * 70)
        lines.append('## %s  [%d肢/%d正解]  stem=%d字' % (q['id'], len(q['options']), q['n_correct'], len(q['question'])))
        lines.append('Q: ' + clean(q['question']))
        for o in q['options']:
            e = clean(o.get('explanation'))
            if len(e) > LIM:
                e = e[:LIM] + '…'
            lines.append('  %s%s %s' % (o['letter'], '*' if o['correct'] else ' ', clean(o['text'])))
            lines.append('     └ %s' % e)
    p = os.path.join(BASE, '資料', '生成', '_review_v2_batch%d.txt' % (b + 1))
    io.open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print(p, len('\n'.join(lines)))
