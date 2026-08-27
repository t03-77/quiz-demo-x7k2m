# -*- coding: utf-8 -*-
"""O-3 の充足状況を 資料/生成/*_orig*.json から直接測る(ビルド前の確認用)。

使い方: python tools/_nm4_check.py [EXAM ...]        資格ごとの充足率
        python tools/_nm4_check.py --ids <id,...>    個別問題の類似度
"""
import json
import glob
import sys
import collections
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def load_all():
    qs = []
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        qs += json.load(open(f, encoding="utf-8"))
    return qs


def sim(q):
    cor = [o["text"] for o in q["options"] if o.get("correct")]
    wrong = [o["text"] for o in q["options"] if not o.get("correct")]
    if not cor or not wrong:
        return None
    return max(SequenceMatcher(None, c, w).ratio() for c in cor for w in wrong)


def main():
    qs = load_all()
    if "--ids" in sys.argv:
        want = set(sys.argv[sys.argv.index("--ids") + 1].split(","))
        for q in qs:
            if q["id"] in want:
                r = sim(q)
                print(f"{q['id']} {r:.3f} {'OK' if r >= 0.72 else 'NG'}")
        return
    exams = sys.argv[1:] or ["AIP-C01", "MLA-C01", "AIF-C01", "CLF-C02"]
    ok = collections.Counter()
    tot = collections.Counter()
    for q in qs:
        if q.get("set") != "orig" or q.get("type", "choice") != "choice" or not q.get("options"):
            continue
        r = sim(q)
        if r is None:
            continue
        tot[q["exam"]] += 1
        if r >= 0.72:
            ok[q["exam"]] += 1
    for ex in exams:
        print(f"{ex} {ok[ex]}/{tot[ex]} = {100*ok[ex]//tot[ex] if tot[ex] else 0}%")


if __name__ == "__main__":
    main()
