# -*- coding: utf-8 -*-
"""v2チェックリスト§10のうち未測定だった観点(S-9/O-6/O-5)を公式と比較して実測する。"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
js = open(BASE / "data" / "orig.js", encoding="utf-8").read()
n = json.loads(js[js.index("["):js.rindex("]") + 1])
off = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))["questions"]
mine = [q for q in n if q.get("set") == "orig" and q.get("options")]
offc = [q for q in off if q.get("options")]

# S-9: 設定断片(JSON/コード/ログ)を stem に含む問題
CODE = re.compile(r'[{}]|"[A-Za-z]+"\s*:|Effect\s*[:=]|arn:aws|<[a-z]+>|\n\s{4,}\S')
def s9(qs):
    return sum(1 for q in qs if CODE.search(q.get("question", "")))
print("S-9 設定断片: 公式 %d/%d (%.1f%%) / 自作 %d/%d (%.1f%%)" % (
    s9(offc), len(offc), s9(offc) / len(offc) * 100,
    s9(mine), len(mine), s9(mine) / len(mine) * 100))

# O-6: 選択肢本文への理由の混入（〜ため/〜ので が肢に入る）
REASON = re.compile(r"(ため|ので)[、。]")
def o6(qs):
    tot = hit = 0
    for q in qs:
        for o in q["options"]:
            tot += 1
            if REASON.search(o.get("text", "")):
                hit += 1
    return hit, tot
h, t = o6(offc); print("O-6 理由の混入: 公式 %d/%d (%.1f%%)" % (h, t, h / t * 100))
h, t = o6(mine); print("O-6 理由の混入: 自作 %d/%d (%.1f%%)" % (h, t, h / t * 100))

# O-5: 誤答の末尾に自ら負けを認める運用記述
LOSE = re.compile(r"(必要がある|必要になる|増える|増大する|かかる|複雑になる|負荷が高い|時間がかかる|手間がかかる)。?$")
def o5(qs):
    tot = hit = 0
    for q in qs:
        for o in q["options"]:
            if o.get("correct"):
                continue
            tot += 1
            if LOSE.search(o.get("text", "")):
                hit += 1
    return hit, tot
h, t = o5(offc); print("O-5 負けを認める末尾: 公式誤答 %d/%d (%.1f%%)" % (h, t, h / t * 100))
h, t = o5(mine); print("O-5 負けを認める末尾: 自作誤答 %d/%d (%.1f%%)" % (h, t, h / t * 100))

# S-5: 問題文の否定・禁止語（〜できない/〜しない 等の制約語句）が誤答肢にそのまま出ている
# 簡易版: stem に「〜は避け」「〜せずに」「〜しない」がある問題で、その直前の名詞句が誤答肢に出るか
BAN = re.compile(r"([ぁ-ん一-龥A-Za-z0-9 ]{4,16})(?:は避け|を避け|せずに|を使用しない|は使用できない)")
def s5(qs):
    tot = hit = 0
    for q in qs:
        m = BAN.search(q.get("question", ""))
        if not m:
            continue
        tot += 1
        key = m.group(1)[-6:]
        if any(key in o.get("text", "") for o in q["options"] if not o.get("correct")):
            hit += 1
    return hit, tot
h, t = s5(offc); print("S-5 禁止語が誤答肢に: 公式 %d/%d 該当問中" % (h, t))
h, t = s5(mine); print("S-5 禁止語が誤答肢に: 自作 %d/%d 該当問中" % (h, t))
