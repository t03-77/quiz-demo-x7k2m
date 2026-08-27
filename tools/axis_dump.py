# -*- coding: utf-8 -*-
"""軸そろえ作業の対象問題を読みやすい形で出力する。

使い方: python tools/axis_dump.py MLA-C01 [開始index] [件数]
"""
import json
import glob
import re
import sys
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')


def overlap(texts):
    s = [set(WORD.findall(t)) for t in texts if t]
    s = [x for x in s if x]
    if len(s) < 2:
        return 0.0
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else 0.0


def load(exam):
    out = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == exam:
                out[q["id"]] = (Path(f).name, q)
    return out


def main():
    exam = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 999
    low = [x["id"] for x in json.load(open(BASE / "資料" / "生成" / "_low_overlap.json",
                                          encoding="utf-8")) if x["exam"] == exam]
    idx = load(exam)
    for qid in low[start:start + count]:
        f, q = idx[qid]
        print("=" * 90)
        print(f"{qid}  [{f}]  domain={q.get('domain')} level={q.get('level')} "
              f"n_correct={q.get('n_correct')} overlap={overlap([o['text'] for o in q['options']]):.3f}")
        print("Q: " + q["question"])
        for o in q["options"]:
            print(f"  {o['letter']}{'*' if o['correct'] else ' '} ({len(o['text'])}) {o['text']}")
            print(f"      EX: {o.get('explanation','')}")


if __name__ == "__main__":
    main()
