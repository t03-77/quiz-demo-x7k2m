# -*- coding: utf-8 -*-
import json,re,statistics,glob,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
EXAM="DVA-C02"
def load_src():
    qs=[]
    for f in sorted(glob.glob(str(BASE/"資料"/"生成"/(EXAM+"_orig*.json")))):
        for q in json.load(open(f,encoding="utf-8")):
            q["_file"]=Path(f).name; qs.append(q)
    return qs
def load_off():
    d=json.load(open(BASE/"資料"/"変換済み"/"questions_all.json",encoding="utf-8"))
    off=d.get("questions",d) if isinstance(d,dict) else d
    return [q for q in off if q.get("set") in("exam","pretest") and q.get("options") and q.get("exam")==EXAM]
def sentences(t): return [s for s in re.split(r"(?<=[。？！])",t or "") if s.strip()]
WORD=re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def stats(qs,label):
    ns=[];cor2=cortot=wr2=wrtot=0
    for q in qs:
        for o in q.get("options") or []:
            t=(o.get("text") or "").strip()
            if not t: continue
            n=len(sentences(t)); ns.append(n)
            if o.get("correct"):
                cortot+=1; cor2+= (n>=2)
            else:
                wrtot+=1; wr2+= (n>=2)
    two=100*sum(1 for x in ns if x>=2)/max(1,len(ns))
    vals=[]
    for q in qs:
        sets=[set(WORD.findall(o.get("text",""))) for o in (q.get("options") or []) if o.get("text")]
        sets=[s for s in sets if s]
        if len(sets)<2: continue
        pr=[len(sets[i]&sets[j])/len(sets[i]|sets[j]) for i in range(len(sets)) for j in range(i+1,len(sets)) if (sets[i]|sets[j])]
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
    lens=[len(o["text"]) for q in qs for o in (q.get("options") or []) if o.get("text")]
    print("%-11s Q=%-4d 肢=%-5d 2文以上=%5.1f%% (正解肢%5.1f%% 誤答肢%5.1f%%)  重なり=%.3f  最長が正解=%5.1f%%  肢中央値%d字"%(
        label,len(qs),len(ns),two,100*cor2/max(1,cortot),100*wr2/max(1,wrtot),ov,100*hi/max(1,t),statistics.median(lens)))
    return dict(two=two,ov=ov,hi=100*hi/max(1,t),n=len(ns),n2=sum(1 for x in ns if x>=2))
if __name__=="__main__":
    o=stats(load_off(),"公式DVA")
    src=load_src(); m=stats(src,"自作DVA")
    print("自作: 2文以上の肢 %d/%d"%(m["n2"],m["n"]))
    # ファイル別内訳
    from collections import Counter
    c=Counter()
    for q in src:
        n2=sum(1 for o in q["options"] if len(sentences(o["text"]))>=2)
        c[q["_file"]]+=n2
    tot=Counter()
    for q in src: tot[q["_file"]]+=len(q["options"])
    for f in sorted(tot): print("   %-28s %3d/%3d"%(f,c[f],tot[f]))
