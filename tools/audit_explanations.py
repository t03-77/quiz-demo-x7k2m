# -*- coding: utf-8 -*-
"""解説の分量を公式模試の水準と比較する。

解説が短いと「なぜ間違えたのか」が分からず、復習しても伸びない。
公式模試の解説(選択肢あたり平均250〜550字)を基準に、資格ごとの達成度を出す。
"""
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REF = re.compile(r"^.*(に関するページを参照してください|を参照してください)。?\s*$", re.M)


def clean(s):
    return REF.sub("", s or "").strip()


def official_baseline():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    out = defaultdict(list)
    for q in d["questions"]:
        if q["set"] not in ("exam", "pretest") or q["type"] != "choice":
            continue
        for o in q["options"]:
            out[q["exam"]].append(len(clean(o.get("explanation", ""))))
    return out


def generated():
    out = defaultdict(list)
    for f in sorted((BASE / "資料" / "生成").glob("*_orig*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            for o in q.get("options", []):
                out[q["exam"]].append(len(clean(o.get("explanation", ""))))
    return out


ref, gen = official_baseline(), generated()
print(f"{'資格':<9}{'公式平均':>8}{'生成平均':>8}{'達成率':>8}   判定")
rows = []
for exam in sorted(gen):
    g = int(st.mean(gen[exam]))
    r = int(st.mean(ref[exam])) if ref.get(exam) else 0
    pct = (g / r * 100) if r else 0
    mark = "★ 到達" if pct >= 85 else ("△ もう少し" if pct >= 60 else "✗ 不足")
    rows.append((pct, exam, r, g, mark))
    print(f"{exam:<9}{r:>8}{g:>8}{pct:>7.0f}%   {mark}")
done = sum(1 for p, *_ in rows if p >= 85)
print(f"\n公式水準(85%以上)に到達: {done}/{len(rows)}資格")
