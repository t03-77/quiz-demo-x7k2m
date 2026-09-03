# -*- coding: utf-8 -*-
"""AIF-C01 の誤答肢テキスト/解説を差し替える。正解肢と不変項目は触らない。
使い方: python tools/_aif_ov_apply.py patch.json [--dry]
patch: [{"id":..,"letter":"B","text":..,"expl":..(任意)}, ...]
"""
import copy, glob, json, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
FIX = ["id","exam","set","type","domain","level","question","n_correct"]

def main(patch_path):
    patches=json.load(open(patch_path,encoding="utf-8"))
    files={}; index={}
    for f in sorted(glob.glob(str(GEN/"AIF-C01_orig*.json"))):
        if "_bak" in f: continue
        data=json.loads(Path(f).read_text(encoding="utf-8"))
        files[f]=data
        for q in data: index[q["id"]]=(f,q)
    snap={qid:copy.deepcopy(q) for qid,(f,q) in index.items()}
    errors=[]; touched=set(); n_t=n_e=0; seen=set()
    for p in patches:
        key=(p["id"],p["letter"])
        if key in seen: errors.append("%s: 重複"%(key,)); continue
        seen.add(key)
        if p["id"] not in index: errors.append("%s: 該当なし"%p["id"]); continue
        f,q=index[p["id"]]
        if q.get("exam")!="AIF-C01": errors.append("%s: AIF-C01以外"%p["id"]); continue
        o=[x for x in q["options"] if x["letter"]==p["letter"]]
        if not o: errors.append("%s[%s]: 選択肢なし"%(p["id"],p["letter"])); continue
        o=o[0]
        if o.get("correct"): errors.append("%s[%s]: 正解肢は書き換え禁止"%(p["id"],p["letter"])); continue
        if "text" in p:
            if not p["text"].strip(): errors.append("%s[%s]: text空"%(p["id"],p["letter"])); continue
            if p["text"]!=o["text"]: o["text"]=p["text"]; n_t+=1; touched.add(f)
        if "expl" in p:
            if not p["expl"].lstrip().startswith("不正解"):
                errors.append("%s[%s]: 解説は「不正解です。」で始める"%(p["id"],p["letter"])); continue
            if p["expl"]!=o.get("explanation"): o["explanation"]=p["expl"]; n_e+=1; touched.add(f)
    # 不変項目の検証
    for qid,(f,q) in index.items():
        s=snap[qid]
        for k in FIX:
            if q.get(k)!=s.get(k): errors.append("%s: 不変項目 %s が変化"%(qid,k))
        if len(q["options"])!=len(s["options"]): errors.append("%s: 選択肢数が変化"%qid); continue
        for a,b in zip(q["options"],s["options"]):
            if a["letter"]!=b["letter"] or a["correct"]!=b["correct"]:
                errors.append("%s[%s]: letter/correct が変化"%(qid,b["letter"]))
            if b["correct"] and (a["text"]!=b["text"] or a.get("explanation")!=b.get("explanation")):
                errors.append("%s[%s]: 正解肢が変化"%(qid,b["letter"]))
    if errors:
        print("NG: %d件のため書き込みなし"%len(errors))
        for e in errors[:30]: print("  "+e)
        return 1
    if "--dry" in sys.argv:
        print("(--dry) text %d / expl %d 件, %dファイル"%(n_t,n_e,len(touched))); return 0
    for f in touched:
        Path(f).write_text(json.dumps(files[f],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("OK: 誤答肢テキスト %d件 / 解説 %d件 (%dファイル)"%(n_t,n_e,len(touched)))
    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1]))
