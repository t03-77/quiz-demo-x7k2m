# -*- coding: utf-8 -*-
"""SAA-C03: 既存の1文肢を「操作A。操作B。」の2文へ分割するパッチを生成する。

語の重なりを動かさないため、接続部だけを置換する（「〜し、」→「〜する。」）。
ひらがなの「する」は重なり計算の語彙に入らないので、肢の語の集合は不変になる。
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fukubun_lib import load, sent, GEN, WORD

SPLITS = [
    ("001", "A", "を作成し、", "を作成する。"),
    ("001", "B", "を作成し、", "を作成する。"),
    ("001", "C", "を作成し、", "を作成する。"),
    ("001", "D", "をアタッチし、", "をアタッチする。"),
    ("004", "A", "を配置し、", "を配置する。"),
    ("004", "B", "に変更し、", "に変更する。"),
    ("004", "C", "を配置し、", "を配置する。"),
    ("004", "D", "に配置し、", "に配置する。"),
    ("007", "A", "を作成し、", "を作成する。"),
    ("007", "B", "を作成し、", "を作成する。"),
    ("007", "C", "を構成して、", "を構成する。"),
    ("007", "D", "を作成し、", "を作成する。"),
    ("012", "A", "を作成し、", "を作成する。"),
    ("012", "B", "に移動して、", "に移動する。"),
    ("012", "C", "に保存し、", "に保存する。"),
    ("012", "D", "を作成し、", "を作成する。"),
    ("038", "A", "として有効化し、", "として有効化する。"),
    ("038", "B", "を作成し、", "を作成する。"),
    ("038", "C", "を集計し、", "を集計する。"),
    ("038", "D", "で出力し、", "で出力する。"),
    ("043", "A", "を構成し、", "を構成する。"),
    ("043", "B", "を開発し、", "を開発する。"),
    ("043", "C", "を有効化して、", "を有効化する。"),
    ("043", "D", "スキャンして、", "スキャンする。"),
    ("086", "A", "を構成し、", "を構成する。"),
    ("086", "B", "を有効にし、", "を有効にする。"),
    ("086", "C", "を有効にし、", "を有効にする。"),
    ("086", "D", "を構成し、", "を構成する。"),
    ("086", "E", "を有効にし、", "を有効にする。"),
    ("087", "A", "を構成し、", "を構成する。"),
    ("087", "B", "を指定し、", "を指定する。"),
    ("087", "C", "スポットインスタンスにし、", "スポットインスタンスにする。"),
    ("087", "D", "に設定して、", "に設定する。"),
    ("087", "E", "を指定し、", "を指定する。"),
]

_, index = load("SAA-C03")
out, bad = [], []
for num, letter, old, new in SPLITS:
    qid = "SAA-C03_orig_%s" % num
    q = index[qid][1]
    o = [x for x in q["options"] if x["letter"] == letter][0]
    if o["text"].count(old) != 1:
        bad.append("%s[%s]: 分割位置 %r が %d 箇所" % (qid, letter, old, o["text"].count(old)))
        continue
    t = o["text"].replace(old, new)
    if len(sent(t)) < 2:
        bad.append("%s[%s]: 2文にならない" % (qid, letter)); continue
    if set(WORD.findall(t)) != set(WORD.findall(o["text"])):
        bad.append("%s[%s]: 語彙が変化 %s" % (qid, letter,
                   set(WORD.findall(t)) ^ set(WORD.findall(o["text"])))); continue
    p = {"id": qid, "letter": letter, "want": 2, "text": t}
    if o["correct"]:
        p["allow_correct"] = True
    out.append(p)
if bad:
    print("NG:")
    for b in bad:
        print("  " + b)
    raise SystemExit(1)
path = GEN / "_fukubun_patch_saa.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("生成 %d件 -> %s" % (len(out), path))
