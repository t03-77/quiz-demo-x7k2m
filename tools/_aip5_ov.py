# -*- coding: utf-8 -*-
"""AIP-C01 の肢どうしの語の重なりを、問題ごとに測る。"""
import json
import glob
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def score(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q.get("options") or []]
    s = [x for x in s if x]
    if len(s) < 2:
        return None
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def main():
    qs = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == "AIP-C01" and q.get("set") == "orig":
                qs[q["id"]] = q
    vals = {i: score(q) for i, q in qs.items()}
    vals = {i: v for i, v in vals.items() if v is not None}
    print("AIP-C01 全体 %.3f (n=%d)" % (statistics.mean(vals.values()), len(vals)))
    if "--list" in sys.argv:
        ids = json.load(open(BASE / "資料" / "生成" / "_aip5.json", encoding="utf-8"))
        for i in sorted(ids, key=lambda x: vals.get(x, 9)):
            print("  %.3f %s" % (vals[i], i))


if __name__ == "__main__":
    main()
