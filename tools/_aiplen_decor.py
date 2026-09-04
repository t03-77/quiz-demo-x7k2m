# -*- coding: utf-8 -*-
"""追加した各文が「どの誤答も落とさない飾り」になっていないかを機械的に洗い出す。
   追加文の内容語が、誤答肢の text/explanation のどれにも掛からない場合は要目視。"""
import json, glob, re, difflib
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
BAK = GEN / "_bak_aiplen_20260904"
STOP = set("同社 同行 同機関 同事務所 同金庫 同大学 必要 場合 内容 使用 実装 運用 現在 社内 対応 以下 こと もの ため 一部 全体 状態 処理 結果 設定 方法 構成 情報 データ".split())

def load(d):
    o = {}
    for f in sorted(glob.glob(str(Path(d) / "AIP-C01_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            o[q["id"]] = q
    return o

def words(t):
    return {w for w in re.findall(r"[A-Za-z][A-Za-z0-9]{2,}|[ァ-ヶー]{3,}|[一-龥]{2,}", t) if w not in STOP}

old, new = load(BAK), load(GEN)
flag = 0
for qid in sorted(old):
    a, b = old[qid]["question"], new[qid]["question"]
    if a == b:
        continue
    # 追加された文だけを取り出す
    added = "".join(x[2:] for x in difflib.ndiff(a, b) if x.startswith("+ "))
    sents = [s for s in re.split(r"(?<=。)", added) if len(s.strip()) >= 12]
    wrong = " ".join((o.get("text", "") + o.get("explanation", ""))
                     for o in new[qid]["options"] if not o.get("correct"))
    ww = words(wrong)
    for s in sents:
        hit = words(s) & ww
        if len(hit) < 2:
            flag += 1
            print(f"[要確認] {qid}: {s.strip()[:60]}  掛かった語={sorted(hit)}")
print(f"\n誤答に掛からない追加文: {flag}件")
