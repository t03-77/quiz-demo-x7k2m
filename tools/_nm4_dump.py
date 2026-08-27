# -*- coding: utf-8 -*-
"""O-3(正解と1点だけ違う誤答)作業用: 候補問題を読みやすく出力する。

使い方: python tools/_nm4_dump.py <EXAM> <開始index> <件数> [--full]
--full を付けると解説も出す。
"""
import json
import glob
import sys
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
SKIP_FILE = "mixed_orig_b1.json"


def load(exam):
    idx = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        if Path(f).name == SKIP_FILE:
            continue
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == exam:
                idx[q["id"]] = (Path(f).name, q)
    return idx


def main():
    exam = sys.argv[1]
    full = "--full" in sys.argv
    idx = load(exam)
    if sys.argv[2] == "ids":
        ids = [i for i in sys.argv[3].split(",")]
    else:
        start = int(sys.argv[2])
        cnt = int(sys.argv[3])
        cand = json.load(open(GEN / "_need_nearmiss.json", encoding="utf-8"))[exam]
        ids = [i for i in cand if i in idx][start:start + cnt]
    for qid in ids:
        fn, q = idx[qid]
        cor = [o["text"] for o in q["options"] if o["correct"]]
        wrong = [o["text"] for o in q["options"] if not o["correct"]]
        r = max(SequenceMatcher(None, c, w).ratio() for c in cor for w in wrong)
        print(f"=== {qid}  [{fn}] type={q.get('type','choice')} n_correct={q.get('n_correct')} domain={q.get('domain')} sim={r:.2f}")
        print("Q: " + q["question"])
        for o in q["options"]:
            mark = "O" if o["correct"] else "x"
            print(f"  {mark} {o['letter']}({len(o['text'])}): {o['text']}")
            if full:
                print(f"      expl({len(o.get('explanation') or '')}): {o.get('explanation')}")
        print()


if __name__ == "__main__":
    main()
