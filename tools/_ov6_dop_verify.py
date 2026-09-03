# -*- coding: utf-8 -*-
"""DOP-C02 の全問を _bak_overlap4_dop_20260903 と突き合わせ、不変項目が動いていないか確認する。"""
import glob
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
BAK = GEN / "_bak_overlap4_dop_20260903"
FIXED = ["id", "exam", "set", "type", "domain", "level", "question", "n_correct"]


def load(d):
    out = {}
    for f in sorted(glob.glob(str(Path(d) / "DOP-C02_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            out[q["id"]] = (Path(f).name, q)
    return out


cur, bak = load(GEN), load(BAK)
errs, changed = [], 0
if set(cur) != set(bak):
    errs.append("ID 集合が違う: 増 %s / 減 %s" % (sorted(set(cur) - set(bak)), sorted(set(bak) - set(cur))))
for qid in sorted(set(cur) & set(bak)):
    fc, a = cur[qid]
    fb, b = bak[qid]
    if fc != fb:
        errs.append("%s ファイルが違う %s != %s" % (qid, fc, fb))
    for k in FIXED:
        if a.get(k) != b.get(k):
            errs.append("%s %s が変わっている" % (qid, k))
    if set(a) != set(b):
        errs.append("%s キー構成が変わっている" % qid)
    if len(a["options"]) != len(b["options"]):
        errs.append("%s 選択肢の数が変わっている" % qid)
        continue
    diff = False
    for oa, ob in zip(a["options"], b["options"]):
        if oa["letter"] != ob["letter"]:
            errs.append("%s letter の並びが変わっている" % qid)
        if oa["correct"] != ob["correct"]:
            errs.append("%s %s correct が変わっている" % (qid, oa["letter"]))
        if set(oa) != set(ob):
            errs.append("%s %s 肢のキー構成が変わっている" % (qid, oa["letter"]))
        if oa["correct"]:
            if oa["text"] != ob["text"]:
                errs.append("%s %s 正解肢の text が変わっている" % (qid, oa["letter"]))
            if oa.get("explanation") != ob.get("explanation"):
                errs.append("%s %s 正解肢の explanation が変わっている" % (qid, oa["letter"]))
        elif oa["text"] != ob["text"] or oa.get("explanation") != ob.get("explanation"):
            diff = True
    if diff:
        changed += 1
print("照合 %d問 / 誤答を書き換えた問題 %d問" % (len(cur), changed))
if errs:
    print("★エラー %d件" % len(errs))
    for e in errs[:40]:
        print("  " + e)
else:
    print("不変項目はすべて一致")
