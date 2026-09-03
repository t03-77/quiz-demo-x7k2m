# -*- coding: utf-8 -*-
import importlib.util, sys, json
spec=importlib.util.spec_from_file_location("m","tools/_aif_ov_measure.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
qs={q["id"]:q for q in m.load()}
for qid in sys.argv[1:]:
    q=qs[qid]
    print("="*78)
    print("%s  [%s] ov=%.3f  n_correct=%d  domain=%s level=%s"%(qid,q["_file"],m.overlap(q),q["n_correct"],q.get("domain"),q.get("level")))
    print("Q: "+q["question"])
    for o in q["options"]:
        print("  %s%s (%d字/%d文) %s"%(o["letter"], "*" if o.get("correct") else " ", len(o["text"]), len(m.sentences(o["text"])), o["text"]))
        print("      expl: "+(o.get("explanation") or ""))
