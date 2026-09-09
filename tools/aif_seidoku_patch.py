# -*- coding: utf-8 -*-
"""AIF-C01 精読修正の適用。options[].text / options[].explanation だけを書き換える。
不変項目(id/exam/set/type/domain/level/question/n_correct/letter/correct)を照合し、
1件でも違えば何も書かずに中断する。書式は無改変ラウンドトリップ(indent=2/CRLF/末尾改行)を検証してから保存。
"""
import json, sys, os, glob

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '資料', '生成')
FILES = sorted(glob.glob(os.path.join(BASE, 'AIF-C01_orig*.json')))
INVARIANT = ('id', 'exam', 'set', 'type', 'domain', 'level', 'question', 'n_correct')


def load(path):
    b = open(path, 'rb').read()
    d = json.loads(b.decode('utf-8'))
    s = (json.dumps(d, ensure_ascii=False, indent=2).replace('\n', '\r\n') + '\r\n').encode('utf-8')
    if s != b:
        raise SystemExit('FORMAT MISMATCH (roundtrip not byte-identical): ' + path)
    return d, b


def dump(d):
    return (json.dumps(d, ensure_ascii=False, indent=2).replace('\n', '\r\n') + '\r\n').encode('utf-8')


def apply(patches, dry=False):
    """patches: list of dict(id, letter, field, old_sub, new_sub)  ※old_sub は部分文字列(ユニーク必須)"""
    idx = {}
    data = {}
    for p in FILES:
        d, b = load(p)
        data[p] = d
        for q in d:
            idx[q['id']] = (p, q)

    snap = {}
    for p in FILES:
        for q in data[p]:
            snap[q['id']] = (tuple(str(q.get(k)) for k in INVARIANT),
                             tuple((o['letter'], bool(o.get('correct'))) for o in q['options']))

    changed = set()
    n = 0
    for pt in patches:
        if pt['id'] not in idx:
            raise SystemExit('NO SUCH ID: ' + pt['id'])
        path, q = idx[pt['id']]
        op = [o for o in q['options'] if o['letter'] == pt['letter']]
        if len(op) != 1:
            raise SystemExit('NO SUCH LETTER: %s %s' % (pt['id'], pt['letter']))
        op = op[0]
        cur = op[pt['field']]
        c = cur.count(pt['old_sub'])
        if c != 1:
            raise SystemExit('OLD_SUB count=%d (must be 1): %s %s %s\n---%s' % (c, pt['id'], pt['letter'], pt['field'], pt['old_sub']))
        op[pt['field']] = cur.replace(pt['old_sub'], pt['new_sub'])
        changed.add(path)
        n += 1

    # invariant check
    for p in FILES:
        for q in data[p]:
            cur = (tuple(str(q.get(k)) for k in INVARIANT),
                   tuple((o['letter'], bool(o.get('correct'))) for o in q['options']))
            if cur != snap[q['id']]:
                raise SystemExit('INVARIANT VIOLATION: ' + q['id'])

    if dry:
        print('DRY-RUN ok: %d patches, files=%s' % (n, sorted(os.path.basename(x) for x in changed)))
        return
    for p in sorted(changed):
        open(p, 'wb').write(dump(data[p]))
    print('applied %d patches to %d files' % (n, len(changed)))


if __name__ == '__main__':
    src = sys.argv[1]
    patches = json.load(open(src, encoding='utf-8'))
    apply(patches, dry=('--dry' in sys.argv))
