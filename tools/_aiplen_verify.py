# -*- coding: utf-8 -*-
"""バックアップと突き合わせ、question 以外が不変であることを確認する。
対象問以外の question 変更、および question 以外の変更は「外部変更」として報告する。"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
BAK = GEN / "_bak_aiplen_20260904"
TARGET = set(json.load(open(GEN / "_aip_short.json", encoding="utf-8"))) | set(json.load(open(GEN / "_aiplen_extra.json", encoding="utf-8")))

def load(d):
    out = {}
    for f in sorted(glob.glob(str(Path(d) / "AIP-C01_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            out[q["id"]] = (Path(f).name, q)
    return out

old, new = load(BAK), load(GEN)
errs, ext, changed = [], [], []
if set(old) != set(new):
    errs.append(f"id集合が違う: 消失{sorted(set(old)-set(new))} 追加{sorted(set(new)-set(old))}")
for qid in sorted(set(old) & set(new)):
    (fo, a), (fn, b) = old[qid], new[qid]
    if fo != fn:
        errs.append(f"{qid}: ファイルが変わった {fo}->{fn}")
    if set(a) != set(b):
        errs.append(f"{qid}: キー構成が変わった {set(a) ^ set(b)}")
    for k in set(a) & set(b):
        if a[k] == b[k]:
            continue
        if k == "question":
            (changed if qid in TARGET else errs).append(
                (qid, len(a[k]), len(b[k])) if qid in TARGET else f"{qid}: 対象外なのに question が変わった")
        else:
            ext.append(f"{qid}: {k}")
print(f"question 変更(対象問内): {len(changed)}問")
for c in changed:
    print(f"   {c[0]}  {c[1]}字 -> {c[2]}字")
if ext:
    print(f"\n[外部変更 = 自分の作業以外で question 以外が動いたもの] {len(ext)}件")
    for e in ext:
        print("   " + e)
if errs:
    print("\n!! 違反 %d 件" % len(errs))
    for e in errs[:40]:
        print("   ", e)
    sys.exit(1)
print("\n対象問について: id/exam/set/type/domain/level/n_correct/options すべて不変")
