"""v2レビュー用: 公式問題から前回未読の100問をバランスサンプリングする一時スクリプト。"""
import json, io, os, re, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, '資料', '変換済み', 'questions_all.json')

PREV = set()
for ex, st, nums in [
    ('SAA-C03', 'exam', [4, 18, 32, 46, 59, 3]),
    ('SAP-C02', 'exam', [4, 18, 32, 46, 59, 2]),
    ('DOP-C02', 'exam', [4, 18, 32, 46, 59, 31]),
    ('SCS-C03', 'pretest', [4, 18, 32, 46, 59, 3]),
    ('DEA-C01', 'exam', [4, 18, 32, 46, 59, 6]),
    ('SOA-C03', 'exam', [8, 22, 37, 51, 63, 15]),
    ('DVA-C02', 'exam', [8, 22, 37, 51, 63, 7]),
    ('MLA-C01', 'exam', [8, 22, 37, 51, 63, 15]),
    ('CLF-C02', 'exam', [8, 22, 37, 51, 63, 19]),
    ('AIF-C01', 'exam', [8, 22, 37, 51, 63, 9]),
    ('AIP-C01', 'pretest', [8]),
]:
    for n in nums:
        PREV.add('%s_%s_%03d' % (ex, st, n))

AX = re.compile(r'最も|最小限|最大限|最小化|最大化|最少|最小の|最大の')

d = json.load(io.open(SRC, encoding='utf-8'))
qs = [q for q in d['questions']
      if q.get('set') in ('exam', 'pretest') and q.get('type') == 'choice'
      and q['id'] not in PREV]

EXAMS = sorted(set(q['exam'] for q in qs))
HAS3 = ['AIP-C01', 'DEA-C01', 'DOP-C02', 'SAP-C02', 'SCS-C03', 'SOA-C03']


def shape(q):
    return (len(q['options']), q['n_correct'])


def pick_spread(pool, n, want_axis=None):
    """長さで三分位に散らし、評価軸有無も混ぜて n 件選ぶ"""
    if not pool or n <= 0:
        return []
    pool = sorted(pool, key=lambda q: len(q['question']))
    out = []
    if want_axis is None:
        # 半々で軸あり/なしを取る
        ax = [q for q in pool if AX.search(q['question'])]
        nax = [q for q in pool if not AX.search(q['question'])]
        na = min(len(ax), (n + 1) // 2)
        nn = min(len(nax), n - na)
        out += pick_even(ax, na) + pick_even(nax, nn)
        rest = [q for q in pool if q not in out]
        out += pick_even(rest, n - len(out))
    else:
        out = pick_even(pool, n)
    return out


def pick_even(pool, n):
    if n <= 0 or not pool:
        return []
    pool = sorted(pool, key=lambda q: (len(q['question']), q['id']))
    if n >= len(pool):
        return list(pool)
    idx = [round(i * (len(pool) - 1) / (n - 1)) if n > 1 else len(pool) // 2 for i in range(n)]
    seen, out = set(), []
    for i in idx:
        while i in seen:
            i = (i + 1) % len(pool)
        seen.add(i)
        out.append(pool[i])
    return out


selected = []
for ex in EXAMS:
    sub = [q for q in qs if q['exam'] == ex]
    s41 = [q for q in sub if shape(q) == (4, 1)]
    s52 = [q for q in sub if shape(q) == (5, 2)]
    s63 = [q for q in sub if shape(q) == (6, 3)]
    n63 = 1 if ex in HAS3 and s63 else 0
    n41 = 6 if n63 else 7
    if ex == 'SAA-C03':
        n41 += 1  # 100問に合わせる
    got = pick_spread(s41, n41) + pick_even(s52, 2) + pick_even(s63, n63)
    selected += got

selected.sort(key=lambda q: (q['exam'], q['id']))
print('total', len(selected))
print(collections.Counter(shape(q) for q in selected))
print(collections.Counter(q['exam'] for q in selected))
print('axis', sum(1 for q in selected if AX.search(q['question'])))
ls = sorted(len(q['question']) for q in selected)
print('len', ls[0], ls[len(ls) // 4], ls[len(ls) // 2], ls[3 * len(ls) // 4], ls[-1])

out = os.path.join(BASE, '資料', '生成', '_review_v2_sample.json')
json.dump({'ids': [q['id'] for q in selected], 'questions': selected},
          io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', out)
