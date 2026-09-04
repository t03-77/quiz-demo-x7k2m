# -*- coding: utf-8 -*-
"""原文を読み込み、指定位置に文脈を差し込んで question パッチを作る。
   原文を打ち直さないので写し間違いが起きない。
   EDITS[id] = [(アンカー文字列, "after"/"before", 差し込む文), ...]
"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"

def load():
    idx = {}
    for f in sorted(glob.glob(str(GEN / "AIP-C01_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            idx[q["id"]] = q
    return idx

def build(edits, outpath):
    idx = load()
    out = []
    for qid, ops in edits.items():
        q = idx[qid]["question"]
        orig_len = len(q)
        for anchor, where, text in ops:
            if q.count(anchor) != 1:
                raise SystemExit(f"{qid}: アンカーが{q.count(anchor)}回出現 -> {anchor[:30]}")
            q = q.replace(anchor, anchor + text if where == "after" else text + anchor)
        out.append({"id": qid, "before": idx[qid]["question"][:12], "question": q})
        print(f"{qid}  {orig_len} -> {len(q)}")
    Path(outpath).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
