# -*- coding: utf-8 -*-
"""どの問題を組み直すかの計画と、鉄則8の事前予測"""
TARGET = """008 009 010 023 025 027 033 034 035 036 040
041 042 043 044 045 046 047 050 051 054 055 057 058 059 060 062 064 066 067
073 074 079 083 093 094 301 302 304 305""".split()
IDS = ["SAP-C02_orig_%s" % t for t in TARGET]
if __name__ == "__main__":
    import json, glob, re, statistics
    def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
    qs = []
    for f in sorted(glob.glob("資料/生成/SAP-C02_orig*.json")):
        qs += json.load(open(f, encoding="utf-8"))
    idx = {q["id"]: q for q in qs}
    assert all(i in idx for i in IDS), [i for i in IDS if i not in idx]
    n = sum(len(q["options"]) for q in qs)
    two = sum(1 for q in qs for o in q["options"] if len(sent(o["text"])) >= 2)
    conv = sum(1 for i in IDS for o in idx[i]["options"] if len(sent(o["text"])) < 2)
    # 対象問題は全肢1文なので、全肢が2文になる
    c_n = sum(1 for q in qs for o in q["options"] if o["correct"])
    w_n = n - c_n
    c2 = sum(1 for q in qs for o in q["options"] if o["correct"] and len(sent(o["text"])) >= 2)
    w2 = two - c2
    dc = sum(1 for i in IDS for o in idx[i]["options"] if o["correct"] and len(sent(o["text"])) < 2)
    dw = conv - dc
    print("組み直す問題 %d問 / 肢 %d" % (len(IDS), conv))
    print("before 2文以上 %d/%d = %.1f%% (表示 %d)" % (two, n, 100*two/n, 100*two//n))
    print("予測   2文以上 %d/%d = %.1f%% (表示 %d)" % (two+conv, n, 100*(two+conv)/n, 100*(two+conv)//n))
    print("  正解肢 %.1f%% -> %.1f%%  (公式 81.8%%)" % (100*c2/c_n, 100*(c2+dc)/c_n))
    print("  誤答肢 %.1f%% -> %.1f%%  (公式 85.8%%)" % (100*w2/w_n, 100*(w2+dw)/w_n))
    rest = [q for q in qs if q["id"] not in IDS]
    fully1 = [q for q in rest if all(len(sent(o["text"])) < 2 for o in q["options"])]
    mixed = [q for q in rest if 0 < sum(1 for o in q["options"] if len(sent(o["text"])) < 2) < len(q["options"])]
    print("残る 全肢1文の問題 %d問(%.1f%%, 公式8.0%%) / 混在 %d問(%.1f%%, 公式13.3%%)"
          % (len(fully1), 100*len(fully1)/len(qs), len(mixed), 100*len(mixed)/len(qs)))
    print("残す(全肢1文のまま): %s" % ", ".join(q["id"][-3:] for q in fully1))
    L = [len(o["text"]) for q in qs for o in q["options"]]
    print("肢長 中央 %d (公式124)。1文肢の中央 %d、2文肢の中央 %d"
          % (statistics.median(L),
             statistics.median([len(o["text"]) for q in qs for o in q["options"] if len(sent(o["text"]))==1]),
             statistics.median([len(o["text"]) for q in qs for o in q["options"] if len(sent(o["text"]))>=2])))
