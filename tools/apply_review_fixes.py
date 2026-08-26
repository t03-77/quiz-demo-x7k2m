# -*- coding: utf-8 -*-
"""独立レビューで指摘された誤りを修正する(2026-08-26 実施)。

いずれもAWS公式ドキュメントで裏を取ったうえでの修正。
実行は冪等で、対象文字列が既に修正済みならスキップする。
"""
import json
from pathlib import Path

GEN = Path(__file__).resolve().parent.parent / "資料" / "生成"

# (ファイル, 問題ID, 選択肢, 対象フィールド, 修正前の一部, 修正後の全文)
FIXES = [
    (
        "DEA-C01_orig_b2.json", "DEA-C01_orig_031", "C", "explanation",
        "SNS、SQS、Lambda であり",
        "不正解です。S3 イベント通知が直接サポートする送信先は SNS、SQS、Lambda、"
        "EventBridge の 4 種類で、Step Functions を直接指定することはできません。"
        "Step Functions を起動するには、選択肢 A のように EventBridge を経由します。",
    ),
    (
        "SAP-C02_orig_b2.json", "SAP-C02_orig_014", "B", "explanation",
        "プライベート VIF の数には制限があり",
        "不正解です。専用接続あたりのプライベート仮想インターフェイスは 50 まで作成できるため "
        "30 本自体は上限内に収まりますが、VPC ごとに仮想インターフェイスと仮想プライベートゲートウェイを"
        "個別に管理することになり、仮想インターフェイスを増やさないという要件に反します。"
        "VPC の追加や変更のたびに接続設定の作業が発生し、運用負荷も高くなります。",
    ),
    (
        "SCS-C03_orig_b3.json", "SCS-C03_orig_057", "A", "text",
        "対象リージョンの s3.amazonaws.com 経由",
        "キーポリシーの許可ステートメントに kms:ViaService 条件キーを追加し、"
        "s3.<リージョン>.amazonaws.com 経由のリクエストのみにキーの使用を限定する。",
    ),
    (
        "SCS-C03_orig_b3.json", "SCS-C03_orig_057", "A", "explanation",
        "正解です。kms:ViaService 条件キーは",
        "正解です。kms:ViaService 条件キーは、KMS へのリクエストが指定した AWS サービスから"
        "プリンシパルに代わって行われた場合にのみ許可 (または拒否) する制御を実現します。"
        "値は s3.us-east-1.amazonaws.com のようにリージョンを含む形式で指定します。"
        "S3 経由に限定すれば、認証情報を窃取した攻撃者が KMS API を直接呼び出してもキーを使用できなくなります。",
    ),
]

applied, skipped = 0, 0
for fname, qid, letter, field, marker, new in FIXES:
    path = GEN / fname
    qs = json.load(open(path, encoding="utf-8"))
    hit = False
    for q in qs:
        if q["id"] != qid:
            continue
        for o in q["options"]:
            if o["letter"] != letter:
                continue
            hit = True
            if marker in o[field]:
                o[field] = new
                applied += 1
                print(f"修正: {qid} 選択肢{letter} の {field}")
            else:
                skipped += 1
                print(f"スキップ(修正済みか対象文字列なし): {qid} 選択肢{letter} の {field}")
    if not hit:
        print(f"警告: 対象が見つかりません {qid} 選択肢{letter}")
    path.write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"\n適用 {applied}件 / スキップ {skipped}件")
