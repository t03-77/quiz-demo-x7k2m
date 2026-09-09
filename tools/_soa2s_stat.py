# -*- coding: utf-8 -*-
import json,re,glob,statistics
from pathlib import Path
from collections import Counter
BASE=Path(__file__).resolve().parent.parent
EXAM="SOA-C03"
def sent(t): return [s for s in re.split(r"(?<=[。？！])",t or "") if s.strip()]
src=[]
for f in sorted(glob.glob(str(BASE/"資料"/"生成"/(EXAM+"_orig*.json")))):
    for q in json.load(open(f,encoding="utf-8")):
        if q.get("exam")==EXAM: q["_f"]=Path(f).name; src.append(q)
d=json.load(open(BASE/"資料"/"変換済み"/"questions_all.json",encoding="utf-8"))
off=[q for q in (d.get("questions",d) if isinstance(d,dict) else d) if q.get("set") in("exam","pretest") and q.get("options") and q.get("exam")==EXAM]
# per-question distribution of #2sent options
def dist(qs,label):
    c=Counter()
    for q in qs:
        n=sum(1 for o in q["options"] if len(sent(o.get("text") or ""))>=2)
        c[(n,len(q["options"]))]+=1
    print(label, sorted(c.items()))
dist(off,"公式(2文肢数,肢数)->問数:")
dist(src,"自作(2文肢数,肢数)->問数:")
# length of sentences in official 2-sent options
oL=[len(o["text"]) for q in off for o in q["options"] if len(sent(o["text"]))>=2]
o1=[len(o["text"]) for q in off for o in q["options"] if len(sent(o["text"]))==1]
sL=[len(o["text"]) for q in src for o in q["options"] if len(sent(o["text"]))>=2]
s1=[len(o["text"]) for q in src for o in q["options"] if len(sent(o["text"]))==1]
print("公式 2文肢の長さ 中央%d 平均%.1f / 1文肢 中央%d 平均%.1f"%(statistics.median(oL),statistics.mean(oL),statistics.median(o1),statistics.mean(o1)))
print("自作 2文肢の長さ 中央%d 平均%.1f / 1文肢 中央%d 平均%.1f"%(statistics.median(sL),statistics.mean(sL),statistics.median(s1),statistics.mean(s1)))
print("公式 全肢 中央%d 平均%.1f  自作 全肢 中央%d 平均%.1f"%(
  statistics.median(oL+o1),statistics.mean(oL+o1),statistics.median(sL+s1),statistics.mean(sL+s1)))
# candidates: questions with 0 two-sent options, list with file
zs=[q for q in src if sum(1 for o in q["options"] if len(sent(o["text"]))>=2)==0]
print("2文肢ゼロの問題数:",len(zs))
c=Counter(q["_f"] for q in zs); print(dict(c))
print("うち肢数4:",sum(1 for q in zs if len(q["options"])==4),"肢数5:",sum(1 for q in zs if len(q["options"])==5))
