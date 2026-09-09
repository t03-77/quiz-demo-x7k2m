# -*- coding: utf-8 -*-
"""パッチ案を当てずに評価する。O-3・語の重なり・複文率・最長が正解 を before/after で出す。
使い方: python tools/_o3b_try.py CLF-C02 資料/生成/_o3b_clf_01.json [...]"""
import json, sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import (load_mine, load_off, overlap, maxsim, sentences, metrics, show)

exam = sys.argv[1]
base = load_mine(exam)
after = copy.deepcopy(base)
idx = {q["id"]: q for q in after}
patch = []
for f in [a for a in sys.argv[2:] if not a.startswith("--")]:
    patch += json.load(open(f, encoding="utf-8"))
bad = []
for p in patch:
    q = idx.get(p["id"])
    if not q:
        bad.append("%s: 未知のid" % p["id"])
        continue
    if q.get("_ro"):
        bad.append("%s: 書換禁止ファイル(%s)" % (p["id"], q["_file"]))
        continue
    o = [x for x in q["options"] if x["letter"] == p["letter"]]
    if not o:
        bad.append("%s[%s]: 選択肢なし" % (p["id"], p["letter"]))
        continue
    if o[0].get("correct"):
        bad.append("%s[%s]: **正解肢**" % (p["id"], p["letter"]))
        continue
    if "text" in p:
        o[0]["text"] = p["text"]
    if "explanation" in p:
        o[0]["explanation"] = p["explanation"]
if bad:
    print("パッチ不正:")
    for b in bad:
        print("  " + b)
    sys.exit(1)

bi = {q["id"]: q for q in base}
print("%-20s %-3s %13s %13s %11s %s" % ("id", "let", "最大類似", "重なり", "文数", "判定"))
for p in patch:
    b, a = bi[p["id"]], idx[p["id"]]
    mb, ma = maxsim(b), maxsim(a)
    ob, oa = overlap(b), overlap(a)
    sb = len(sentences([x for x in b["options"] if x["letter"] == p["letter"]][0]["text"]))
    sa = len(sentences([x for x in a["options"] if x["letter"] == p["letter"]][0]["text"]))
    ng = []
    if ma >= 0.72:
        ng.append("O-3残")
    if sa != sb:
        ng.append("文数変化")
    if oa < ob - 0.06:
        ng.append("重なり減%.3f" % (ob - oa))
    print("%-20s %-3s %5.2f->%5.2f %5.3f->%5.3f %4d->%4d %s"
          % (p["id"], p["letter"], mb, ma, ob, oa, sb, sa, "  ".join(ng) or "ok"))

B, A, O = metrics(base), metrics(after), metrics(load_off(exam))
print()
show([("before", B), ("after", A), (exam[:7] + "公式", O)])
lim = O["ov"] * 0.9
print()
print("重なり★不足の下限(公式x0.9) = %.4f / after = %.4f -> %s"
      % (lim, A["ov"], "OK" if A["ov"] >= lim or O["ov"] - A["ov"] < 0.03 else "★NG"))
print("重なり★超過の上限(公式/0.9) = %.4f -> %s"
      % (O["ov"] / 0.9, "OK" if A["ov"] <= O["ov"] / 0.9 or A["ov"] - O["ov"] < 0.03 else "★NG"))
