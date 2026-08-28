# -*- coding: utf-8 -*-
"""指定した問題IDを書き直し作業用に読みやすく出す。

使い方: python tools/qdump_ids.py ID [ID ...]
"""
import json
import glob
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load():
    idx = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            idx[q["id"]] = q
    return idx


def main():
    idx = load()
    for qid in sys.argv[1:]:
        q = idx.get(qid)
        if not q:
            print(f"### {qid}: 該当なし")
            continue
        cor = [o for o in q["options"] if o["correct"]]
        cmean = statistics.mean(len(o["text"]) for o in cor)
        cmax = max(len(o["text"]) for o in cor)
        print(f"### {q['id']}  n_correct={q['n_correct']}  domain={q.get('domain')}"
              f"  ★誤答の目安 {int(0.85*cmean)}〜{int(1.15*cmean)}字 (正解最長 {cmax}字)")
        print(f"Q: {q['question']}")
        for o in q["options"]:
            mark = "○正解" if o["correct"] else "×誤答"
            print(f"{o['letter']} {mark} ({len(o['text'])}字) {o['text']}")
            if not o["correct"]:
                print(f"   解説({len(o.get('explanation',''))}字): {o.get('explanation','')}")
        print()


if __name__ == "__main__":
    main()
