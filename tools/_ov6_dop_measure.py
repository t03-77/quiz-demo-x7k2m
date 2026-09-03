# -*- coding: utf-8 -*-
"""DOP-C02 の「肢どうしの語の重なり」と「最長が正解」を 資料/生成 から直接測る。
使い方: python tools/_ov6_dop_measure.py [ディレクトリ]
"""
import glob
import json
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
EXAM = "DOP-C02"


def overlap(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    if len(s) < 2:
        return None
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def load(d):
    ids = {}
    for f in sorted(glob.glob(str(Path(d) / "DOP-C02_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("set") != "orig" or q.get("exam") != EXAM or not q.get("options"):
                continue
            ids[q["id"]] = (Path(f).name, q)
    return ids


def stats(ids):
    vals, longest, n = {}, 0, 0
    for qid, (fn, q) in ids.items():
        v = overlap(q)
        if v is not None:
            vals[qid] = v
        opts = q["options"]
        cor = [o for o in opts if o.get("correct")]
        wrong = [o for o in opts if not o.get("correct")]
        if cor and wrong:
            n += 1
            if max(len(o.get("text", "")) for o in opts) == max(len(o.get("text", "")) for o in cor):
                longest += 1
    return vals, longest, n


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else str(BASE / "資料" / "生成")
    ids = load(d)
    vals, longest, n = stats(ids)
    print("%s  重なり %.3f (%d問)  最長が正解 %.1f%% (%d/%d)"
          % (d, statistics.mean(vals.values()), len(vals), 100.0 * longest / n, longest, n))
