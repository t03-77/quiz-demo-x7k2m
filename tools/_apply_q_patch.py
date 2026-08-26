# -*- coding: utf-8 -*-
"""Apply question-text-only patches to 資料/生成/SAP-C02_orig*.json.

Usage: python tools/_apply_q_patch.py <patch.json>
patch.json: {"<id>": "<new question text>", ...}
Only the "question" field is modified; everything else is preserved verbatim.
"""
import json
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, '資料', '生成')


def main():
    patch_path = sys.argv[1]
    with open(patch_path, encoding='utf-8') as f:
        patch = json.load(f)

    remaining = dict(patch)
    for path in sorted(glob.glob(os.path.join(GEN, 'SAP-C02_orig*.json'))):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        changed = False
        for q in data:
            if q['id'] in remaining:
                new = remaining.pop(q['id'])
                old = q['question']
                q['question'] = new
                changed = True
                print('%s: %d -> %d chars' % (q['id'], len(old), len(new)))
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
            print('  saved: %s' % os.path.basename(path))

    if remaining:
        print('NOT FOUND: %s' % ', '.join(remaining))
        sys.exit(1)


if __name__ == '__main__':
    main()
