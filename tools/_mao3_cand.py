# -*- coding: utf-8 -*-
"""候補テキストを id[letter] ごとに一括採点する（MLA-C01 / AIF-C01）。
入力 JSON: [{"id":..., "letter":..., "cands":["案1","案2",...]}, ...]
出力: 案ごとに 正解肢との最大類似 / その問の重なり差分 / 文数 / 孤立語
使い方: python tools/_mao3_cand.py MLA-C01 資料/生成/_mao3_cand.json"""
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1]
os.environ["O3EXAM"] = EX
import _mao3_lib as L
L.set_exam(EX)

data = json.load(open(sys.argv[2], encoding="utf-8"))
idx = {q["id"]: q for q in L.load_mine()}
for d in data:
    q = idx[d["id"]]
    o = [x for x in q["options"] if x["letter"] == d["letter"]][0]
    if o.get("correct"):
        raise SystemExit("中断: %s[%s] は正解肢" % (d["id"], d["letter"]))
    old = o["text"]
    others = [set(L.WORD.findall(x["text"])) for x in q["options"] if x["letter"] != d["letter"]]
    pool = set().union(*others) if others else set()
    ob, mb, sb = L.overlap(q), L.maxsim(q), len(L.sentences(old))
    print("\n== %s[%s] before: max=%.3f ov=%.3f 文=%d 字=%d" % (d["id"], d["letter"], mb, ob, sb, len(old)))
    print("     旧: %s" % old)
    for c in d["cands"]:
        o["text"] = c
        ma, oa = L.maxsim(q), L.overlap(q)
        iso = sorted(set(L.WORD.findall(c)) - pool)
        lost = sorted((set(L.WORD.findall(old)) & pool) - set(L.WORD.findall(c)))
        print("  max=%.3f ov=%+.3f 文=%d 字=%d 孤立%d [%s] / 消えた共有語[%s]"
              % (ma, oa - ob, len(L.sentences(c)), len(c), len(iso), " ".join(iso), " ".join(lost)))
        print("     %s" % c)
    o["text"] = old
