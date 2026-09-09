# -*- coding: utf-8 -*-
"""パッチ案の肢について、語の重なり(Jaccard)を落としている原因を語単位で示す。
- 消えた共有語 : 元の肢にあり他の肢とも共有していたのに、新しい肢から消えた語
- 増えた孤立語 : 新しい肢にしかない語(和集合だけ増やして共通部分を増やさない = 重なりを下げる)
- 拾える語     : 他の肢にあるのに新しい肢にない語(入れれば重なりが上がる候補)
使い方: python tools/_o3b_tok.py SOA-C03 資料/生成/_o3b_soa_01.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import load_mine, WORD, overlap

exam = sys.argv[1]
patch = []
for a in sys.argv[2:]:
    patch += json.load(open(a, encoding="utf-8"))
idx = {q["id"]: q for q in load_mine(exam)}
tot_b = tot_a = 0.0
for p in patch:
    q = idx[p["id"]]
    o = [x for x in q["options"] if x["letter"] == p["letter"]][0]
    old, new = o["text"], p.get("text", o["text"])
    others = [set(WORD.findall(x["text"])) for x in q["options"] if x["letter"] != p["letter"]]
    pool = set().union(*others) if others else set()
    so, sn = set(WORD.findall(old)), set(WORD.findall(new))
    ob = overlap(q)
    o["text"] = new
    oa = overlap(q)
    o["text"] = old
    tot_b += ob; tot_a += oa
    print("\n== %s[%s] 重なり %.3f -> %.3f (%+.3f)" % (p["id"], p["letter"], ob, oa, oa - ob))
    lost = sorted((so & pool) - sn)
    iso = sorted(sn - pool)
    pick = sorted(pool - sn)
    print("  消えた共有語(%d): %s" % (len(lost), " ".join(lost)))
    print("  増えた孤立語(%d): %s" % (len(iso), " ".join(iso)))
    print("  拾える語(%d): %s" % (len(pick), " ".join(pick)))
print("\n合計 %.3f -> %.3f (%+.3f) / 対象%d肢" % (tot_b, tot_a, tot_a - tot_b, len(patch)))
