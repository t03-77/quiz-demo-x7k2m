# -*- coding: utf-8 -*-
"""S-5: 問題文の「再作成せずに」に真っ向から反する誤答E(2問)を制約内の誤答へ差し替える。
誤答肢の text と explanation のみ変更。正解肢・フラグ・問題文は不変。"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FIX = {
    "AIP-C01_orig_303": {
        "E": {
            "text": "各ドキュメントの本文冒頭に製品シリーズ名の見出しを追記して、データソースを同期する。Retrieve API の検索設定でメタデータフィルターを指定し、選択したシリーズの文書だけを検索対象にする。",
            "explanation": "不正解です。メタデータフィルターで参照できるのは、ドキュメントごとのメタデータファイルなどで属性として登録された値です。本文の冒頭にシリーズ名を書き足しても、検索対象のテキストの一部になるだけで、フィルター条件に使える属性にはなりません。シリーズで絞り込むには、メタデータファイルで属性を付与してからデータソースを同期する必要があります。",
        },
    },
    "AIP-C01_orig_354": {
        "E": {
            "text": "検索タイプをハイブリッド検索に変更する。ベクトル類似度に語句の完全一致によるキーワード検索のスコアを組み合わせて、正解となるチャンクの順位が全体的に上がるようにする。",
            "explanation": "不正解です。ハイブリッド検索は、型番や専門用語のような語句の完全一致を含む問い合わせで検索の取りこぼしを減らすのには有効です。しかし、取得済みの候補チャンクをクエリとの関連性で並べ直す仕組みではないため、「正解チャンクの順位が低い」という 1 つ目の問題への対処としては再ランキングに及ばず、複数の論点を含む質問で片方しか回答されないという 2 つ目の問題にも対処できません。",
        },
    },
}

changed = 0
for f in glob.glob(str(BASE / "資料" / "生成" / "AIP-C01_orig*.json")):
    if "_bak" in f:
        continue
    data = json.load(open(f, encoding="utf-8"))
    dirty = False
    for q in data:
        if q["id"] in FIX:
            for o in q["options"]:
                fx = FIX[q["id"]].get(o["letter"])
                if fx:
                    assert not o["correct"], "正解肢に書き込もうとした: " + q["id"]
                    o["text"] = fx["text"]
                    o["explanation"] = fx["explanation"]
                    dirty = True
                    changed += 1
    if dirty:
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
        print("updated:", Path(f).name)
print("changed options:", changed)
