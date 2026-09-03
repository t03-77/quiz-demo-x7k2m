# -*- coding: utf-8 -*-
import json,re,statistics,glob,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
def load_src():
    qs=[]
    for f in sorted(glob.glob(str(BASE/"資料"/"生成"/"SCS-C03_orig*.json"))):
        d=json.load(open(f,encoding="utf-8"))
        arr=d.get("questions",d) if isinstance(d,dict) else d
        for q in arr: q["_file"]=f
        qs+=arr
    return qs
def load_off():
    d=json.load(open(BASE/"資料"/"変換済み"/"questions_all.json",encoding="utf-8"))
    off=d.get("questions",d) if isinstance(d,dict) else d
    return [q for q in off if q.get("set") in("exam","pretest") and q.get("options") and q.get("exam")=="SCS-C03"]
def sentences(t): return [s for s in re.split(r"(?<=[。？！])",t or "") if s.strip()]
WORD=re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def stats(qs,label):
    ns=[]
    for q in qs:
        for o in q.get("options") or []:
            t=(o.get("text") or "").strip()
            if t: ns.append(len(sentences(t)))
    two=100*sum(1 for x in ns if x>=2)/max(1,len(ns))
    vals=[]
    for q in qs:
        sets=[set(WORD.findall(o.get("text",""))) for o in (q.get("options") or []) if o.get("text")]
        sets=[s for s in sets if s]
        if len(sets)<2: continue
        pr=[]
        for i in range(len(sets)):
            for j in range(i+1,len(sets)):
                u=sets[i]|sets[j]
                if u: pr.append(len(sets[i]&sets[j])/len(u))
        if pr: vals.append(statistics.mean(pr))
    ov=statistics.mean(vals) if vals else 0
    hi=lo=same=0
    for q in qs:
        op=q.get("options") or []
        cor=[len(o["text"]) for o in op if o.get("correct")]; wr=[len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr: continue
        m=max(cor+wr); a=max(cor)==m; b=max(wr)==m
        if a and not b: hi+=1
        elif b and not a: lo+=1
        else: same+=1
    t=hi+lo+same
    print("%-12s Q=%-4d 肢=%-5d 2文以上=%5.1f%%  重なり=%.3f  最長が正解=%5.1f%%"%(label,len(qs),len(ns),two,ov,100*hi/max(1,t)))
    return two,ov,100*hi/max(1,t)
if __name__=="__main__":
    stats(load_off(),"公式SCS")
    src=load_src(); stats(src,"自作SCS")
