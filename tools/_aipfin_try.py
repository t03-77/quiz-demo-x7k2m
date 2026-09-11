# -*- coding: utf-8 -*-
"""候補テキストを当てはめたときの 重なり / 最大類似 / hi-lo / 文数 / 字数 / kwleak を採点する。
使い方: python -X utf8 tools/_aipfin_try.py <patch.json>   （書き込みはしない）"""
import json, sys, statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sao3_lib import load_mine, sentences
from _aipfin_measure import ovq, maxsim, hilo, kwleak

mine = load_mine("AIP-C01")
idx = {q["id"]: q for q in mine}
patch = []
for a in sys.argv[1:]:
    patch += json.load(open(a, encoding="utf-8"))
targets = sorted({p["id"] for p in patch})
print("%-22s %-28s %-28s" % ("id", "before", "after"))
for qid in targets:
    q = idx[qid]
    b = (ovq(q), maxsim(q), hilo(q), kwleak(q),
         [len(o["text"]) for o in q["options"]],
         [len(sentences(o["text"])) for o in q["options"]])
    for p in patch:
        if p["id"] != qid: continue
        o = [x for x in q["options"] if x["letter"] == p["letter"]][0]
        assert not o.get("correct"), "正解肢: " + qid + p["letter"]
        if "text" in p: o["text"] = p["text"]
    a = (ovq(q), maxsim(q), hilo(q), kwleak(q),
         [len(o["text"]) for o in q["options"]],
         [len(sentences(o["text"])) for o in q["options"]])
    print("%-22s ov %.4f sim %.3f %-4s kw%d %s %s" % (qid, b[0], b[1], b[2], b[3], b[4], b[5]))
    print("%-22s ov %.4f sim %.3f %-4s kw%d %s %s%s" % ("", a[0], a[1], a[2], a[3], a[4], a[5],
          "   <<< 薄い" if a[0] < 0.1 else ""))
ovs = [v for v in (ovq(q) for q in mine) if v is not None]
ms = [v for v in (maxsim(q) for q in mine) if v is not None]
hl = [hilo(q) for q in mine]
ns = [len(sentences(o["text"])) for q in mine for o in q["options"] if o.get("text")]
thin = sum(1 for v in ovs if v < 0.1)
print()
print("全体(適用後): 重なり %.4f | 薄い %d問 %.1f%%(表示%d%%) | O-3 %.1f%% | >=0.60 %.1f%% | 複文 %.1f%% | hi %.1f%% lo %.1f%% same %.1f%% | kwleak %d問"
      % (statistics.mean(ovs), thin, 100*thin/len(ovs), 100*thin//len(ovs),
         100*sum(1 for m in ms if m >= .72)/len(ms), 100*sum(1 for m in ms if m >= .60)/len(ms),
         100*sum(1 for x in ns if x >= 2)/len(ns),
         100*hl.count("hi")/len(hl), 100*hl.count("lo")/len(hl), 100*hl.count("same")/len(hl),
         sum(1 for q in mine if kwleak(q))))
