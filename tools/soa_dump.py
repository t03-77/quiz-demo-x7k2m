# -*- coding: utf-8 -*-
"""SOA-C03 の問題を書き直し作業用に読みやすい形で出す。

使い方: python tools/soa_dump.py <開始番号> <件数> [--noexpl]
番号は誤答肢の書き直し対象(choice形式)を id 順に並べたときの通し番号。
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load():
    qs = []
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == "SOA-C03" and q.get("type", "choice") == "choice":
                qs.append(q)
    qs.sort(key=lambda q: q["id"])
    return qs


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    noexpl = "--noexpl" in sys.argv
    qs = load()
    for i, q in enumerate(qs[start:start + count], start=start):
        cor = [o for o in q["options"] if o["correct"]]
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        cmax = max(len(o["text"]) for o in cor)
        print(f"### [{i}] {q['id']}  n_correct={q['n_correct']}  {q['domain']}"
              f"  ★誤答の目安 {int(0.85*cmean)}〜{int(1.15*cmean)}字 / どれか1つは {cmax+3}字以上")
        print(f"Q: {q['question']}")
        needy = "--needy" in sys.argv
        for o in q["options"]:
            mark = "○正解" if o["correct"] else "×誤答"
            inband = 0.8 * cmean <= len(o["text"]) <= 1.2 * cmean
            tag = "" if o["correct"] else ("  [範囲内]" if inband else "  [要修正]")
            print(f"{o['letter']} {mark} ({len(o['text'])}字){tag} {o['text']}")
            if o["correct"] or noexpl:
                continue
            if needy and inband:
                continue
            print(f"   解説({len(o.get('explanation',''))}字): {o.get('explanation','')}")
        print()


if __name__ == "__main__":
    main()
