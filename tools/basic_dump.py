# -*- coding: utf-8 -*-
"""基礎資格 (AIF-C01 / CLF-C02) の問題を誤答肢そろえ作業用に出す。

使い方:
  python tools/basic_dump.py AIF-C01 --ids 005,007,010 [--noexpl]
  python tools/basic_dump.py AIF-C01 --need          # 手当てが要る問題の一覧だけ
"""
import json
import glob
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load(exam):
    qs = []
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == exam and q.get("type", "choice") == "choice":
                qs.append(q)
    qs.sort(key=lambda q: q["id"])
    return qs


def stats(q):
    cor = [o for o in q["options"] if o["correct"]]
    wr = [o for o in q["options"] if not o["correct"]]
    cmean = statistics.mean(len(o["text"]) for o in cor)
    cmax = max(len(o["text"]) for o in cor)
    wmean = statistics.mean(len(o["text"]) for o in wr)
    longest = cmax >= max(len(o["text"]) for o in q["options"])
    return cmean, cmax, wmean, longest


def main():
    exam = sys.argv[1]
    qs = load(exam)
    noexpl = "--noexpl" in sys.argv

    if "--need" in sys.argv:
        for q in qs:
            cmean, cmax, wmean, longest = stats(q)
            r = cmean / wmean
            if r >= 1.30 or (longest and r >= 1.15):
                print(f"{q['id'][-3:]} r={r:.2f} 正解{cmean:.0f}/{cmax} "
                      f"誤答目安 {int(0.85*cmean)}〜{int(1.15*cmean)}字 "
                      f"[{','.join(str(len(o['text'])) for o in q['options'])}]")
        return

    want = None
    if "--ids" in sys.argv:
        want = set(sys.argv[sys.argv.index("--ids") + 1].split(","))
    for q in qs:
        num = q["id"].rsplit("_", 1)[-1]
        if want is not None and num not in want:
            continue
        cmean, cmax, wmean, longest = stats(q)
        print(f"### {q['id']}  n_correct={q['n_correct']}  {q.get('domain')}  "
              f"★誤答の目安 {int(0.85*cmean)}〜{int(1.15*cmean)}字 (正解 平均{cmean:.0f}/最長{cmax})")
        print(f"Q({len(q['question'])}字): {q['question']}")
        for o in q["options"]:
            mark = "○正解" if o["correct"] else "×誤答"
            print(f"{o['letter']} {mark} ({len(o['text'])}字) {o['text']}")
            if not noexpl:
                print(f"   解説({len(o.get('explanation',''))}字): {o.get('explanation','')}")
        print()


if __name__ == "__main__":
    main()
