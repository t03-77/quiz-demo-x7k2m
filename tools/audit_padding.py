# -*- coding: utf-8 -*-
"""解説が「字数合わせの水増し」になっていないかを検査する。

字数を目標にすると、中身のない一文を足して数字だけ満たす失敗が起きうる。
水増しの兆候を機械的に拾って、人が確認すべき候補を絞り込む。
"""
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"

# 中身が薄くなりがちな決まり文句
FILLER = [
    "重要です", "注意が必要です", "理解しておく必要があります", "覚えておきましょう",
    "適切ではありません", "望ましくありません", "推奨されません", "一般的です",
    "さまざまな", "多くの場合", "場合によっては",
]

texts = []
for f in sorted(GEN.glob("*_orig*.json")):
    for q in json.load(open(f, encoding="utf-8")):
        for o in q.get("options", []):
            texts.append((q["id"], o["letter"], (o.get("explanation") or "").strip()))

print(f"検査した選択肢: {len(texts)}個\n")

# 1) 決まり文句の多用
filler_hits = []
for qid, letter, t in texts:
    n = sum(t.count(w) for w in FILLER)
    if n >= 3:
        filler_hits.append((n, qid, letter))
filler_hits.sort(reverse=True)
print(f"■ 決まり文句が3つ以上: {len(filler_hits)}件")
for n, qid, letter in filler_hits[:8]:
    print(f"   {qid}[{letter}] {n}箇所")

# 2) 同一文の使い回し(定型文を貼り付けて字数を稼いでいないか)
sents = Counter()
for _, _, t in texts:
    for s in re.split(r"(?<=。)", t):
        s = s.strip()
        if len(s) >= 25:
            sents[s] += 1
dup = [(c, s) for s, c in sents.items() if c >= 4]
dup.sort(reverse=True)
print(f"\n■ 4回以上使い回されている文: {len(dup)}件")
for c, s in dup[:8]:
    print(f"   {c}回: {s[:70]}")

# 3) 同じ解説内での文の重複
selfdup = []
for qid, letter, t in texts:
    ss = [s.strip() for s in re.split(r"(?<=。)", t) if len(s.strip()) >= 20]
    if len(ss) != len(set(ss)):
        selfdup.append((qid, letter))
print(f"\n■ 同じ解説の中で同一文が繰り返されている: {len(selfdup)}件")
for qid, letter in selfdup[:8]:
    print(f"   {qid}[{letter}]")
