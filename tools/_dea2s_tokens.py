# -*- coding: utf-8 -*-
"""旧肢の技術トークンが新肢に残っているかを全数走査（バックアップと現行を突き合わせ）"""
import json, glob, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
BAK = GEN / "_bak_dea_fukubun"
TOK = re.compile(r"[A-Za-z][A-Za-z0-9_.:*-]{2,}|[ァ-ヶー]{3,}|[一-龥]{2,}")
STOP = {"AWS","Amazon","する","使用","作成","設定","構成","有効","指定","追加","実行","変更",
        "データ","テーブル","ジョブ","対象","処理","利用","参照","出力","保存","取得","以降",
        "アクセス","クラスター","バケット","ロール","ポリシー","場合","方法","内容","結果"}
def load(d):
    idx={}
    for f in sorted(glob.glob(str(Path(d)/"DEA-C01_orig*.json"))):
        for q in json.load(open(f,encoding="utf-8")):
            if q.get("exam")=="DEA-C01": idx[q["id"]]=q
    return idx
old, new = load(BAK), load(GEN)
rows=[]
for qid,oq in old.items():
    nq=new[qid]
    for oo,no in zip(oq["options"], nq["options"]):
        if oo["text"]==no["text"]: continue
        ot=set(TOK.findall(oo["text"]))-STOP
        nt=set(TOK.findall(no["text"]))-STOP
        lost=sorted(ot-nt)
        if lost:
            rows.append({"id":qid,"letter":oo["letter"],"correct":oo["correct"],
                         "lost":lost,"old":oo["text"],"new":no["text"]})
print("書き換えた肢: %d / トークンが落ちた肢: %d (うち正解肢 %d)" % (
    sum(1 for qid,oq in old.items() for oo,no in zip(oq["options"],new[qid]["options"]) if oo["text"]!=no["text"]),
    len(rows), sum(1 for r in rows if r["correct"])))
for r in rows:
    print("\n%s[%s]%s 落ちた: %s" % (r["id"], r["letter"], "*正解" if r["correct"] else "", "、".join(r["lost"])))
    print("  旧: %s" % r["old"])
    print("  新: %s" % r["new"])
