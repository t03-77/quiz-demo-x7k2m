# -*- coding: utf-8 -*-
"""O-3(正解と1点だけ違う誤答)の書き直し候補を読みやすく出す。

使い方: python tools/_nearmiss_dump.py <EXAM> <開始番号> <件数> [--noexpl]
候補は 資料/生成/_need_nearmiss.json のID順。
"""
import json
import glob
import sys
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def load(exam):
    qs = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        if "_bak" in f:
            continue
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == exam and q.get("type", "choice") == "choice":
                qs[q["id"]] = q
    return qs


def main():
    exam = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    noexpl = "--noexpl" in sys.argv
    cand = json.load(open(GEN / "_need_nearmiss.json", encoding="utf-8"))[exam]
    qs = load(exam)
    ids = [i for i in cand if i in qs]
    for i, qid in enumerate(ids[start:start + count], start=start):
        q = qs[qid]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        sims = {o["letter"]: max(SequenceMatcher(None, c["text"], o["text"]).ratio() for c in cor)
                for o in wrong}
        print(f"### [{i}] {qid}  n_correct={q['n_correct']}  {q.get('domain')}")
        print(f"Q: {q['question']}")
        for o in q["options"]:
            mark = "○正解" if o["correct"] else f"×誤答(類似{sims[o['letter']]:.2f})"
            print(f"{o['letter']} {mark} ({len(o['text'])}字) {o['text']}")
            if not o["correct"] and not noexpl:
                print(f"   解説({len(o.get('explanation',''))}字): {o.get('explanation','')}")
        print()


if __name__ == "__main__":
    main()
