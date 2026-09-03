# -*- coding: utf-8 -*-
import json, sys
c=json.load(open(sys.argv[1],encoding="utf-8"))
out=[]
for q,d in c.items():
    for L,v in d.items():
        p={"id":q,"letter":L}
        if isinstance(v,str): p["text"]=v
        else: p.update(v)
        out.append(p)
open(sys.argv[2],"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
print("patches:",len(out))
