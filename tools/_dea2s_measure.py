# -*- coding: utf-8 -*-
"""DEA-C01 の複文率と副作用指標を、資料/生成のソースから直接測る（ビルド不要）"""
import json, glob, re, statistics, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
EXAM = "DEA-C01"
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

def load_mine(d=None):
    qs = []
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / (EXAM + "_orig*.json")))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == EXAM and q.get("set") == "orig" and q.get("options"):
                qs.append(q)
    return qs

def load_off():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options") and q.get("exam") == EXAM]

def metrics(qs, label):
    ns = []
    for q in qs:
        for o in q["options"]:
            t = (o.get("text") or "").strip()
            if t: ns.append(len(sent(t)))
    two = 100 * sum(1 for x in ns if x >= 2) // max(1, len(ns))
    # overlap
    vals = []
    for q in qs:
        ss = [set(WORD.findall(o.get("text",""))) for o in q["options"] if o.get("text")]
        ss = [s for s in ss if s]
        pr = [len(ss[i]&ss[j])/len(ss[i]|ss[j]) for i in range(len(ss)) for j in range(i+1,len(ss)) if (ss[i]|ss[j])]
        if pr: vals.append(statistics.mean(pr))
    ovm = round(statistics.mean(vals), 3) if vals else 0
    # longest correct
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
    # lengths
    olen = [len(o["text"]) for q in qs for o in q["options"] if o.get("text")]
    qlen = [len(q.get("question","")) for q in qs]
    elen = [len(o.get("explanation") or "") for q in qs for o in q["options"] if (o.get("explanation") or "").strip()]
    # keyword leak: 問題文の語が正解肢だけに出る
    leak = 0
    for q in qs:
        qw = set(WORD.findall(q.get("question","")))
        cor = set(); wrong = set()
        for o in q["options"]:
            (cor if o.get("correct") else wrong).update(WORD.findall(o.get("text","")))
        if (qw & cor) - wrong - {"AWS","Amazon"}: leak += 1
    r = {
        "問数": len(qs), "肢数": len(ns),
        "複文率%": two,
        "1肢あたり文数(中央)": statistics.median(ns) if ns else 0,
        "重なり": ovm,
        "最長が正解%": round(100*hi/t,1) if t else 0,
        "最長が誤答%": round(100*lo/t,1) if t else 0,
        "肢長(中央)": statistics.median(olen) if olen else 0,
        "問題文(中央)": statistics.median(qlen) if qlen else 0,
        "解説(中央)": statistics.median(elen) if elen else 0,
        "キーワード直結%": round(100*leak/max(1,len(qs)),1),
    }
    print("[%s] %s" % (label, json.dumps(r, ensure_ascii=False)))
    return r

if __name__ == "__main__":
    metrics(load_off(), "公式")
    metrics(load_mine(), "自作")
