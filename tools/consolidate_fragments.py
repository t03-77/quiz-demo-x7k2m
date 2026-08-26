# -*- coding: utf-8 -*-
"""中断で残った断片ファイル(_frag*.json / _tmp_p*.json)を正規の {EXAM}_orig_bN.json に統合する。

ビルドスクリプトは *_orig*.json しか読まないため、アンダースコア始まりの断片は
そのままでは取り込まれない。試験ごとにID順で結合し、30問ずつのファイルに詰め直す。
"""
import json
import re
from collections import defaultdict
from pathlib import Path

GEN = Path(__file__).resolve().parent.parent / "資料" / "生成"

frags = defaultdict(list)
sources = []
for f in sorted(GEN.glob("_*.json")):
    qs = json.load(open(f, encoding="utf-8"))
    for q in qs:
        frags[q["exam"]].append(q)
    sources.append(f)

if not frags:
    print("統合対象の断片なし")
    raise SystemExit

for exam, qs in frags.items():
    qs.sort(key=lambda q: int(re.search(r"_(\d+)$", q["id"]).group(1)))
    # 既存の正規ファイルに入っているIDは重複させない
    have = set()
    for f in GEN.glob(f"{exam}_orig*.json"):
        for q in json.load(open(f, encoding="utf-8")):
            have.add(q["id"])
    fresh = [q for q in qs if q["id"] not in have]
    if not fresh:
        print(f"{exam}: 断片はすべて既存ファイルに含まれる")
        continue

    # 既存の bN の続き番号から採番
    used = {int(m.group(1)) for f in GEN.glob(f"{exam}_orig_b*.json")
            if (m := re.search(r"_b(\d+)\.json$", f.name))}
    n = max(used) + 1 if used else 2
    for i in range(0, len(fresh), 30):
        chunk = fresh[i:i + 30]
        out = GEN / f"{exam}_orig_b{n}.json"
        out.write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{out.name}: {len(chunk)}問 ({chunk[0]['id']}〜{chunk[-1]['id']})")
        n += 1

for f in sources:
    f.unlink()
print(f"断片 {len(sources)}ファイルを削除")
