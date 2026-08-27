# -*- coding: utf-8 -*-
"""AIP-C01 の1正解5肢 80問を、判断に必要な情報だけ絞って出力する。"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
IDS = json.load(open(BASE / "資料" / "生成" / "_aip5.json", encoding="utf-8"))


def index():
    idx = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            idx[q["id"]] = q
    return idx


def main():
    a = int(sys.argv[1]); b = int(sys.argv[2])
    expl = "--expl" in sys.argv
    idx = index()
    for qid in IDS[a:b]:
        q = idx[qid]
        print("=" * 70)
        print(f"{qid}  domain={q.get('domain')} level={q.get('level')}")
        print(q["question"])
        for o in q["options"]:
            mark = "[正]" if o["correct"] else "[誤]"
            print(f"  {o['letter']}. {mark} {o['text']}")
            if expl:
                print(f"      解説: {o.get('explanation','')}")


if __name__ == "__main__":
    main()
