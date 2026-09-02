# -*- coding: utf-8 -*-
"""D1ファクトチェックの指摘2件（誤答の結論は正しいが解説の断定が古い/強すぎる）を修正。
- DOP-059 D: CloudWatch アラームは Lambda 直接呼び出しもサポート済み（SNSのみは古い）
- DOP-107 C: SCP は aws:PrincipalTag 条件でプリンシパル単位の効果分けが可能（不可能は誤り）
誤答肢の explanation のみ変更。"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

EDITS = [
    ("DOP-C02_orig_059", "D",
     "不正解です。メトリクスフィルターとアラームを組み合わせる構成は要件に沿っています。しかし、CloudWatch アラームの通知アクションが直接サポートする送信先は Amazon SNS トピックであり、Amazon SQS キューを通知先として指定することはできません。オンコール担当者への通知には SNS トピックを設定します。",
     "不正解です。メトリクスフィルターとアラームを組み合わせる構成は要件に沿っています。しかし、CloudWatch アラームのアクションに Amazon SQS キューを直接指定することはできません。通知には SNS トピック (または Lambda 関数の呼び出し) を使用します。オンコール担当者への通知には SNS トピックを設定します。"),
    ("DOP-C02_orig_107", "C",
     "不正解です。SCP は OU やアカウントに属するすべてのプリンシパルへ一律に適用される権限の上限です。同一のアカウントに複数のコストセンターの開発者が混在する環境では、SCP で利用者ごとに制御を変えることはできません。400 のアカウントをコストセンター単位の OU に組み替える作業も現実的ではなく、IdP 側の属性を更新するだけで個人の権限が追従するという要件も満たせません。",
     "不正解です。SCP は OU やアカウント単位でプリンシパル全体に適用される権限の上限であり、利用者ごとに割り当てを分けることはできません。プリンシパルタグの条件で効果を分けることは可能ですが、タグ条件に依存する複雑な設計になります。400 のアカウントをコストセンター単位の OU に組み替える作業も現実的ではなく、IdP 側の属性を更新するだけで個人の権限が追従するという要件も満たせません。"),
]

applied = 0
for f in glob.glob(str(BASE / "資料" / "生成" / "DOP-C02_orig*.json")):
    if "_bak" in f:
        continue
    data = json.load(open(f, encoding="utf-8"))
    dirty = False
    for q in data:
        for qid, letter, old, new in EDITS:
            if q["id"] != qid:
                continue
            o = next(x for x in q["options"] if x["letter"] == letter)
            assert not o["correct"], "正解肢: " + qid
            assert o["explanation"] == old, "解説不一致: " + qid
            o["explanation"] = new
            applied += 1
            dirty = True
    if dirty:
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
        print("updated:", Path(f).name)
print("applied:", applied, "/", len(EDITS))
