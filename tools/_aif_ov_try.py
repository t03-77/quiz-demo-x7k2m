# -*- coding: utf-8 -*-
"""候補テキストを当てはめて、重なり・長さ・文数・最長が正解 を試算する。
使い方: python tools/_aif_ov_try.py cand.json
cand.json: {"AIF-C01_orig_068": {"B": "...", "C": "...", "D": "..."}, ...}
"""
import importlib.util, json, sys, statistics
spec=importlib.util.spec_from_file_location("m","tools/_aif_ov_measure.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
qs={q["id"]:q for q in m.load()}
cand=json.load(open(sys.argv[1],encoding="utf-8"))
tot_before=tot_after=0
for qid,rep in cand.items():
    q=qs[qid]
    before=m.overlap(q)
    texts={o["letter"]:o["text"] for o in q["options"]}
    for L,t in rep.items():
        assert not [o for o in q["options"] if o["letter"]==L and o["correct"]], "%s[%s] は正解肢"%(qid,L)
        texts[L]=t
    fake={"options":[{"letter":L,"text":texts[L],"correct":o["correct"]}
                     for L,o in [(o["letter"],o) for o in q["options"]]]}
    after=m.overlap(fake)
    cor=[len(o["text"]) for o in fake["options"] if o["correct"]]
    wr=[len(o["text"]) for o in fake["options"] if not o["correct"]]
    mx=max(cor+wr); longest_cor = (max(cor)==mx and max(wr)!=mx)
    cor0=[len(o["text"]) for o in q["options"] if o["correct"]]
    wr0=[len(o["text"]) for o in q["options"] if not o["correct"]]
    mx0=max(cor0+wr0); longest_cor0=(max(cor0)==mx0 and max(wr0)!=mx0)
    ns=[len(m.sentences(texts[o["letter"]])) for o in q["options"]]
    cm=statistics.mean(cor); wm=statistics.mean(wr)
    out=[]
    for o in fake["options"]:
        out.append("%s%s=%d/%d文"%(o["letter"],"*" if o["correct"] else "",len(o["text"]),len(m.sentences(o["text"]))))
    print("%s ov %.3f -> %.3f | 最長が正解 %s->%s | 正解平均%.0f 誤答平均%.0f 比%.2f | %s"%(
        qid,before,after,longest_cor0,longest_cor,cm,wm,cm/wm," ".join(out)))
    tot_before+=before; tot_after+=after
print("-- 合計 %.3f -> %.3f (差 %.3f) / 全114問平均への影響 %.4f"%(tot_before,tot_after,tot_after-tot_before,(tot_after-tot_before)/114))
allv=[m.overlap(x) for x in qs.values()]
print("-- 予測 全体平均 %.4f -> %.4f"%(statistics.mean(allv),(sum(allv)+tot_after-tot_before)/len(allv)))
