# -*- coding: utf-8 -*-
"""パッチ案を当てずに評価する（DVA-C02 / DOP-C02）。
O-3・語の重なり・複文率・最長が正解 などを before/after で出す。
使い方: python tools/_dvdo3_try.py DVA-C02 資料/生成/_dvdo3_patch_xx.json [...]"""
import json, sys, os, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1]
os.environ["O3EXAM"] = EX
import _dvdo3_lib as L
L.set_exam(EX)

base = L.load_mine()
after = copy.deepcopy(base)
idx = {q["id"]: q for q in after}
patch = []
for f in [a for a in sys.argv[2:] if not a.startswith("--")]:
    patch += json.load(open(f, encoding="utf-8"))
bad = []
for p_ in patch:
    q = idx.get(p_["id"])
    if not q:
        bad.append("%s: 未知のid" % p_["id"]); continue
    o = [x for x in q["options"] if x["letter"] == p_["letter"]]
    if not o:
        bad.append("%s[%s]: 選択肢なし" % (p_["id"], p_["letter"])); continue
    if o[0].get("correct"):
        bad.append("%s[%s]: **正解肢**" % (p_["id"], p_["letter"])); continue
    if "text" in p_:
        o[0]["text"] = p_["text"]
    if "explanation" in p_:
        o[0]["explanation"] = p_["explanation"]
if bad:
    print("パッチ不正:")
    for b in bad:
        print("  " + b)
    sys.exit(1)

bi = {q["id"]: q for q in base}
print("%-20s %-3s %13s %13s %11s %s" % ("id", "let", "最大類似", "重なり", "文数", "判定"))
seen = []
for p_ in patch:
    if (p_["id"], p_["letter"]) in seen:
        print("  重複パッチ: %s[%s]" % (p_["id"], p_["letter"]))
    seen.append((p_["id"], p_["letter"]))
    b, a = bi[p_["id"]], idx[p_["id"]]
    mb, ma = L.maxsim(b), L.maxsim(a)
    ob, oa = L.overlap(b), L.overlap(a)
    tb = [x for x in b["options"] if x["letter"] == p_["letter"]][0]["text"]
    ta = [x for x in a["options"] if x["letter"] == p_["letter"]][0]["text"]
    sb, sa = len(L.sentences(tb)), len(L.sentences(ta))
    ng = []
    if ma >= 0.72:
        ng.append("O-3残")
    if sa < sb:
        ng.append("文数減")
    if oa < ob - 0.12:
        ng.append("重なり大幅減")
    if len(ta) < len(tb) * 0.7:
        ng.append("字数減")
    print("%-20s %-3s %5.2f->%5.2f %5.3f->%5.3f %4d->%4d %s"
          % (p_["id"], p_["letter"], mb, ma, ob, oa, sb, sa, "  ".join(ng) or "ok"))

B, A, O = L.metrics(base), L.metrics(after), L.metrics(L.load_off())
print()
print("%-18s %9s %9s %9s" % ("指標", "before", "after", EX + "公式"))
for k, lab, f in L.LABELS:
    print(("%-18s " + f + " " + f + " " + f) % (lab, B[k], A[k], O[k]))
print()
print("重なり ★不足の下限(公式x0.9)=%.4f / after=%.4f -> %s"
      % (O["ov"] * 0.9, A["ov"], "OK" if A["ov"] >= O["ov"] * 0.9 else "★NG"))
print("O-3 目標レンジ(公式x0.75〜x1.25)=%.1f%%〜%.1f%% / after=%.1f%%"
      % (O["o3"] * 0.75, O["o3"] * 1.25, A["o3"]))
