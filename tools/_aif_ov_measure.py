# -*- coding: utf-8 -*-
"""AIF-C01 の肢の重なり・2文率・最長が正解 を 資料/生成/*.json 直読みで測る"""
import glob, json, os, re, statistics, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

def sentences(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]

def overlap(q):
    sets = [set(WORD.findall(o.get("text",""))) for o in q.get("options",[]) if o.get("text")]
    sets = [s for s in sets if s]
    if len(sets) < 2: return None
    return statistics.mean([len(sets[i]&sets[j])/len(sets[i]|sets[j])
                            for i in range(len(sets)) for j in range(i+1,len(sets))])

def load(prefix="AIF-C01"):
    out = []
    for f in sorted(glob.glob(str(GEN / (prefix+"_orig*.json")))):
        if "_bak" in f: continue
        for q in json.load(open(f, encoding="utf-8")):
            q["_file"] = os.path.basename(f)
            out.append(q)
    return out

def report(qs, label=""):
    ovs = [(q["id"], overlap(q), q["_file"]) for q in qs]
    ovs = [x for x in ovs if x[1] is not None]
    nsent = []
    for q in qs:
        for o in q["options"]:
            t = (o.get("text") or "").strip()
            if t: nsent.append(len(sentences(t)))
    hi = tot = 0
    for q in qs:
        op = q["options"]
        cor = [len(o["text"]) for o in op if o.get("correct")]
        wr  = [len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr: continue
        tot += 1
        m = max(cor+wr)
        if max(cor)==m and max(wr)!=m: hi += 1
    print("%s 問数=%d" % (label, len(qs)))
    print("  肢どうしの語の重なり: %.3f" % statistics.mean([x[1] for x in ovs]))
    print("  2文以上: %d%% (%d/%d)" % (100*sum(1 for x in nsent if x>=2)//len(nsent),
                                       sum(1 for x in nsent if x>=2), len(nsent)))
    print("  最長が正解: %.1f%% (%d/%d)" % (hi/tot*100, hi, tot))
    return ovs

if __name__ == "__main__":
    qs = load()
    ovs = report(qs, "AIF-C01")
    if "--list" in sys.argv:
        print("\n-- 重なり高い順 top35 --")
        for i,(qid,v,f) in enumerate(sorted(ovs, key=lambda x:-x[1])[:35],1):
            print("%2d. %-20s %.3f  %s" % (i, qid, v, f))
        print("\n-- 誤答肢が2文以上の問題 --")
        for q in qs:
            bad = [o["letter"] for o in q["options"] if not o.get("correct") and len(sentences(o.get("text","")))>=2]
            if bad:
                print("   %-20s %s  %s (ov=%.3f)" % (q["id"], bad, q["_file"], overlap(q)))
        print("\n-- 正解肢が2文以上の問題(不変) --")
        for q in qs:
            bad = [o["letter"] for o in q["options"] if o.get("correct") and len(sentences(o.get("text","")))>=2]
            if bad:
                print("   %-20s %s  %s" % (q["id"], bad, q["_file"]))
