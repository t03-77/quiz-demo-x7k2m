# -*- coding: utf-8 -*-
"""担当5資格の「肢どうしの語の重なり」を資料/生成から直接測る。
使い方: python tools/_ov5_measure.py [ディレクトリ]
省略時は 資料/生成 を見る。バックアップと比較したいときは
  python tools/_ov5_measure.py 資料/_bk_overlap5_before
"""
import glob
import json
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
EX = ["DEA-C01", "SAA-C03", "SAP-C02", "SCS-C03", "DOP-C02"]


def overlap(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    if len(s) < 2:
        return None
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def load(d):
    per = {e: [] for e in EX}
    ids = {}
    for f in sorted(glob.glob(str(Path(d) / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("set") != "orig" or q.get("exam") not in per or not q.get("options"):
                continue
            v = overlap(q)
            if v is None:
                continue
            per[q["exam"]].append(v)
            ids[q["id"]] = v
    return per, ids


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else str(BASE / "資料" / "生成")
    per, ids = load(d)
    allv = []
    for e in EX:
        v = per[e]
        allv += v
        print(f"{e}: {statistics.mean(v):.3f}  ({len(v)}問)")
    print(f"5資格計: {statistics.mean(allv):.3f}  ({len(allv)}問)")
