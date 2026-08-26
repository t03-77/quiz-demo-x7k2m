# -*- coding: utf-8 -*-
"""生成フォルダの全JSONを検証し、資格別の有効問題数と欠番を報告する"""
import json
import re
from collections import defaultdict
from pathlib import Path

GEN = Path(__file__).resolve().parent.parent / "資料" / "生成"

ok_by_exam = defaultdict(set)
broken = []
frag_info = []

for f in sorted(GEN.glob("*.json")):
    try:
        qs = json.load(open(f, encoding="utf-8"))
        if not isinstance(qs, list):
            broken.append((f.name, "配列でない"))
            continue
    except Exception as e:
        broken.append((f.name, f"JSON壊れ: {str(e)[:60]}"))
        continue

    bad = []
    exams = set()
    for q in qs:
        try:
            n = sum(1 for o in q["options"] if o["correct"])
            if n != q["n_correct"] or n == 0:
                bad.append(q.get("id", "?"))
            exams.add(q["exam"])
        except Exception:
            bad.append(q.get("id", "?"))
    if bad:
        broken.append((f.name, f"correct数不一致 {len(bad)}問: {bad[:3]}"))
        continue

    if f.name.startswith("_"):
        frag_info.append((f.name, sorted(exams), len(qs), [q["id"] for q in qs[:1]] + [q["id"] for q in qs[-1:]]))
    for q in qs:
        m = re.search(r"_orig_(\d+)$", q["id"])
        if m:
            ok_by_exam[q["exam"]].add(int(m.group(1)))

print("=== 資格別の有効問題数(正規ファイル+断片) ===")
for exam in sorted(ok_by_exam):
    nums = ok_by_exam[exam]
    missing = sorted(set(range(1, 101)) - nums)
    gaps = f" 欠番{len(missing)}個: {missing[:6]}{'...' if len(missing) > 6 else ''}" if missing else " ★100問完成"
    print(f"{exam}: {len(nums)}問{gaps}")

if frag_info:
    print("\n=== 断片ファイル ===")
    for name, exams, n, ids in frag_info:
        print(f"{name}: {exams} {n}問 {ids}")

if broken:
    print("\n=== 破損/不正ファイル(要再生成) ===")
    for name, why in broken:
        print(f"{name}: {why}")
