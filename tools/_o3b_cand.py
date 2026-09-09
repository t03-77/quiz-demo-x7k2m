# -*- coding: utf-8 -*-
"""候補テキストを id[letter] ごとに一括採点する。
入力 JSON: [{"id":..., "letter":..., "cands":["案1","案2",...]}, ...]
出力: 案ごとに 正解肢との最大類似 / その問の重なり差分 / 文数 / 孤立語数
使い方: python tools/_o3b_cand.py SOA-C03 資料/生成/_o3b_cand.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import load_mine, WORD, overlap, maxsim, sentences

exam = sys.argv[1]
data = json.load(open(sys.argv[2], encoding="utf-8"))
idx = {q["id"]: q for q in load_mine(exam)}
for d in data:
    q = idx[d["id"]]
    o = [x for x in q["options"] if x["letter"] == d["letter"]][0]
    old = o["text"]
    others = [set(WORD.findall(x["text"])) for x in q["options"] if x["letter"] != d["letter"]]
    pool = set().union(*others) if others else set()
    ob, mb, sb = overlap(q), maxsim(q), len(sentences(old))
    print("\n== %s[%s] before: max=%.3f ov=%.3f 文=%d" % (d["id"], d["letter"], mb, ob, sb))
    for c in d["cands"]:
        o["text"] = c
        ma, oa = maxsim(q), overlap(q)
        iso = sorted(set(WORD.findall(c)) - pool)
        print("  max=%.3f ov=%+.3f 文=%d 孤立%d [%s]" % (ma, oa - ob, len(sentences(c)), len(iso), " ".join(iso)))
        print("     %s" % c)
    o["text"] = old
