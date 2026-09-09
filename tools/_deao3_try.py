# -*- coding: utf-8 -*-
"""パッチ案を当てずに評価する。O-3・語の重なり・複文率・最長が正解 を before/after で出す。
使い方: python tools/_deao3_try.py 資料/生成/_deao3_patch_b1.json [...]"""
import json, sys, copy, statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _deao3_lib import load_mine, load_off, pairs, overlap, multi_sent, maxsim, sentences

def longest(qs):
    hi = lo = same = 0
    for q in qs:
        op = q.get("options") or []
        cor = [len(o["text"]) for o in op if o.get("correct")]
        wr = [len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr: continue
        m = max(cor + wr); a = max(cor) == m; b = max(wr) == m
        if a and not b: hi += 1
        elif b and not a: lo += 1
        else: same += 1
    t = hi + lo + same
    return 100*hi/t, 100*lo/t

def metrics(qs):
    ch = [q for q in qs if q.get("type", "choice") == "choice" and q.get("options")]
    ms = [m for m in (maxsim(q) for q in ch) if m is not None]
    ov = [o for o in (overlap(q) for q in ch) if o is not None]
    mm = sum(multi_sent(q)[0] for q in ch); mt = sum(multi_sent(q)[1] for q in ch)
    ln = [len(o["text"]) for q in ch for o in q["options"]]
    hi, lo2 = longest(ch)
    return dict(o3=100*sum(1 for m in ms if m >= .72)/len(ms),
                s60=100*sum(1 for m in ms if m >= .60)/len(ms),
                lo=100*sum(1 for m in ms if m < .50)/len(ms),
                med=statistics.median(ms), ov=statistics.mean(ov),
                fk=100*mm/mt, optlen=statistics.median(ln), hi=hi, lo3=lo2)

base = load_mine()
after = copy.deepcopy(base)
idx = {q["id"]: q for q in after}
patch = []
for f in [a for a in sys.argv[1:] if not a.startswith("--")]:
    patch += json.load(open(f, encoding="utf-8"))
bad = []
for p in patch:
    q = idx.get(p["id"])
    if not q: bad.append("%s: 未知のid" % p["id"]); continue
    o = [x for x in q["options"] if x["letter"] == p["letter"]]
    if not o: bad.append("%s[%s]: 選択肢なし" % (p["id"], p["letter"])); continue
    if o[0].get("correct"): bad.append("%s[%s]: 正解肢" % (p["id"], p["letter"])); continue
    o[0]["_old"] = o[0]["text"]
    if "text" in p: o[0]["text"] = p["text"]
    if "explanation" in p: o[0]["explanation"] = p["explanation"]
if bad:
    print("パッチ不正:"); [print("  "+b) for b in bad]; sys.exit(1)

bi = {q["id"]: q for q in base}
print("%-18s %-3s %13s %13s %13s %s" % ("id", "let", "最大類似", "重なり", "文数", "判定"))
for p in patch:
    b, a = bi[p["id"]], idx[p["id"]]
    mb, ma = maxsim(b), maxsim(a)
    ob, oa = overlap(b), overlap(a)
    sb = len(sentences([x for x in b["options"] if x["letter"] == p["letter"]][0]["text"]))
    sa = len(sentences([x for x in a["options"] if x["letter"] == p["letter"]][0]["text"]))
    ng = []
    if ma >= 0.72: ng.append("O-3残")
    if sa != sb: ng.append("文数変化")
    if oa < ob - 0.12: ng.append("重なり大幅減")
    print("%-18s %-3s %5.2f->%5.2f %5.3f->%5.3f %5d->%5d %s"
          % (p["id"], p["letter"], mb, ma, ob, oa, sb, sa, "  ".join(ng) or "ok"))

B, A = metrics(base), metrics(after)
O = metrics(load_off())
print()
print("%-16s %8s %8s %8s"%("指標","before","after","DEA公式"))
for k, lab, f in [("o3","O-3(>=0.72)","%7.1f%%"),("s60",">=0.60","%7.1f%%"),("lo","<0.50","%7.1f%%"),
                  ("med","最大類似の中央","%8.3f"),("ov","肢の語の重なり","%8.3f"),
                  ("fk","選択肢2文以上","%7.1f%%"),("optlen","選択肢の中央字数","%8.0f"),
                  ("hi","最長が正解","%7.1f%%"),("lo3","最長が誤答","%7.1f%%")]:
    print(("%-16s "+f+" "+f+" "+f) % (lab, B[k], A[k], O[k]))
print()
print("重なり★不足の下限(公式x0.9) = %.4f / after = %.4f  -> %s"
      % (O["ov"]*0.9, A["ov"], "OK" if A["ov"] >= O["ov"]*0.9 or O["ov"]-A["ov"] < 0.03 else "★NG"))
