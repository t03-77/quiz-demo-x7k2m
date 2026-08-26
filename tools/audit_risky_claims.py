# -*- coding: utf-8 -*-
"""生成問題のうち「事実誤認になりやすい記述」を洗い出す。

AWSの数値上限・料金・SLAは改定されるため、断定するとそのまま誤問になる。
該当箇所を一覧化し、人の確認 or 差し替えの対象を絞り込む。
"""
import json
import re
from pathlib import Path

GEN = Path(__file__).resolve().parent.parent / "資料" / "生成"

# 危険度の高い順。ラベル → 正規表現
PATTERNS = [
    ("料金の断定", r"(\$\s?\d|\d+\s*ドル|\d+\s*円|無料枠の\d)"),
    ("SLA/可用性の断定", r"(99\.\d+\s*%|SLA)"),
    ("具体的な上限値", r"(最大\s*[\d,]+\s*(GB|TB|MB|KB|個|件|台|本|回|秒|分|時間|日)|"
                     r"[\d,]+\s*(GB|TB|MB)\s*(まで|以下|以内|が上限)|上限は\s*[\d,]+)"),
    ("時間の断定", r"([\d,]+\s*(秒|分|時間|日)\s*(以内|まで|が上限|に制限))"),
]

rows = []
total = 0
for f in sorted(GEN.glob("*_orig*.json")):
    for q in json.load(open(f, encoding="utf-8")):
        total += 1
        blob = q["question"] + " " + " ".join(
            o["text"] + " " + o.get("explanation", "") for o in q.get("options", []))
        for label, pat in PATTERNS:
            m = re.search(pat, blob)
            if m:
                rows.append((label, q["id"], m.group(0)[:40]))
                break

print(f"検査対象: {total}問")
print(f"要確認: {len(rows)}問 ({len(rows)/max(total,1)*100:.1f}%)\n")
by_label = {}
for label, qid, hit in rows:
    by_label.setdefault(label, []).append((qid, hit))
for label in [p[0] for p in PATTERNS]:
    items = by_label.get(label, [])
    if not items:
        continue
    print(f"■ {label}: {len(items)}問")
    for qid, hit in items[:8]:
        print(f"   {qid}: 「{hit}」")
    if len(items) > 8:
        print(f"   …ほか{len(items)-8}問")
    print()
