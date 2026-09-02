# -*- coding: utf-8 -*-
"""ブラインド消去法テストのサンプル生成。
公式40問+自作40問を層化抽出し、出典を伏せてシャッフルした判定用ファイルと、
採点用の正解マッピングを書き出す。乱数はシード固定で再現可能にする。

usage: python tools/_blind_sample.py
出力: 資料/生成/_blind_questions_YYYYMMDD.json  (判定者に渡す。出典・正解なし)
      資料/生成/_blind_answers_YYYYMMDD.json    (採点用。出典と正解)
"""
import json
import random
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEED = 20260902
STAMP = "20260902"
N_PER_SIDE = 40

js = open(BASE / "data" / "orig.js", encoding="utf-8").read()
mine = [q for q in json.loads(js[js.index("["):js.rindex("]") + 1])
        if q.get("set") == "orig" and q.get("type") == "choice"]
off = [q for q in json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))["questions"]
       if q.get("type") == "choice" and q.get("exam") != "ANS-C01"]

rng = random.Random(SEED)

def stratified(qs, n):
    by_exam = {}
    for q in qs:
        by_exam.setdefault(q["exam"], []).append(q)
    exams = sorted(by_exam)
    per = max(1, n // len(exams))
    picked = []
    for ex in exams:
        picked += rng.sample(by_exam[ex], min(per, len(by_exam[ex])))
    rest = [q for q in qs if q not in picked]
    while len(picked) < n:
        picked.append(rest.pop(rng.randrange(len(rest))))
    return picked[:n]

sample = [("official", q) for q in stratified(off, N_PER_SIDE)] + \
         [("orig", q) for q in stratified(mine, N_PER_SIDE)]
rng.shuffle(sample)

blind, answers = [], []
for i, (src, q) in enumerate(sample, 1):
    opts = list(q["options"])
    rng.shuffle(opts)  # データ上の正解位置の偏りを判定に持ち込まない
    letters = "ABCDEF"
    blind.append({
        "no": i,
        "question": q["question"],
        "options": [{"letter": letters[j], "text": o["text"]} for j, o in enumerate(opts)],
        "n_correct": q.get("n_correct") or sum(1 for o in opts if o["correct"]),
    })
    answers.append({
        "no": i, "source": src, "id": q.get("id"), "exam": q.get("exam"),
        "correct": [letters[j] for j, o in enumerate(opts) if o["correct"]],
    })

out_q = BASE / "資料" / "生成" / f"_blind_questions_{STAMP}.json"
out_a = BASE / "資料" / "生成" / f"_blind_answers_{STAMP}.json"
out_q.write_text(json.dumps(blind, ensure_ascii=False, indent=1), encoding="utf-8")
out_a.write_text(json.dumps(answers, ensure_ascii=False, indent=1), encoding="utf-8")
print("questions:", out_q.name, len(blind), "問 / answers:", out_a.name)
