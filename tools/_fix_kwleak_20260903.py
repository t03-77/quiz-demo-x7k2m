# -*- coding: utf-8 -*-
"""組み直しで発生したキーワード直結4問の解消。
問題文の語が正解肢にだけ出る状態を、誤答肢へ同じ語を自然に織り込んで解消する。
誤答肢 text のみ変更（解説は既に該当用語へ言及しており整合を確認済み）。"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

EDITS = [
    ("MLA-C01_orig_086", "D",
     "各チームが CI/CD パイプライン一式のスタックを個別に作成して環境を再現する",
     "各チームが MLOps 用 CI/CD パイプライン一式のスタックを個別に作成して環境を再現する"),
    ("SAA-C03_orig_087", "E",
     "スポットの割り当て戦略に最低価格 (lowest-price) を指定し",
     "Auto Scaling グループのスポット割り当て戦略に最低価格 (lowest-price) を指定し"),
    ("SCS-C03_orig_076", "D",
     "全アカウントのルートユーザーにパスワードポリシーを適用する",
     "全アカウントのルートユーザーに、MFA の代わりに強力なパスワードポリシーを適用する"),
    ("SOA-C03_orig_101", "C",
     "ノードグループの更新戦略を default から minimal に変更して、追加のノードを起動せずに",
     "ノードグループの更新戦略を default から minimal に変更して、PDB の minAvailable はそのままに、追加のノードを起動せずに"),
    ("SOA-C03_orig_101", "D",
     "ノードグループの最大サイズを引き上げたうえで",
     "Deployment の replicas は変更せずにノードグループの最大サイズを引き上げたうえで"),
]

by_id = {}
for qid, letter, old, new in EDITS:
    by_id.setdefault(qid, []).append((letter, old, new))

applied = 0
for f in glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json")):
    if "_bak" in f:
        continue
    data = json.load(open(f, encoding="utf-8"))
    dirty = False
    for q in data:
        if q["id"] not in by_id:
            continue
        for letter, old, new in by_id[q["id"]]:
            o = next(x for x in q["options"] if x["letter"] == letter)
            assert not o["correct"], "正解肢: %s %s" % (q["id"], letter)
            assert old in o["text"], "置換元不一致: %s %s" % (q["id"], letter)
            o["text"] = o["text"].replace(old, new)
            applied += 1
            dirty = True
    if dirty:
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
        print("updated:", Path(f).name)
print("applied:", applied, "/", len(EDITS))
