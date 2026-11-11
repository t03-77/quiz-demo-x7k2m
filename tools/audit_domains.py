# -*- coding: utf-8 -*-
"""生成問題のドメイン配分を公式試験ガイドの比重と突き合わせる。

試験範囲外・比重の偏った問題を解いても合格には近づかないため、
ドメイン名の表記ゆれと、公式比重からの乖離を検出する。
BLUEPRINT は公式試験ガイド(AWS Certification Exam Guides)の値。
"""
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# 公式試験ガイドのドメイン比重(%)。キーは照合用の短いキーワード
# SOA-C03 / SCS-C03 は 2025年改訂版。docs.aws.amazon.com の試験ガイドで実値を確認済み
# 問題データの exam キーは進捗データを壊さないため SAP-C02 / DVA-C02 のまま（中身は新版に合わせている）
BLUEPRINT = {
    "CLF-C02": {"コンセプト": 24, "セキュリティとコンプライアンス": 30, "テクノロジー": 34, "請求": 12},
    "AIF-C01": {"AI と ML": 20, "生成 AI": 24, "基盤モデル": 28, "責任": 14, "コンプライアンス": 14},
    "SAA-C03": {"セキュア": 30, "弾力": 26, "パフォーマンス": 24, "コスト": 20},
    # DVA は 2026-12-01 開始の DVA-C03 の配点（2026-11-11 に切り替え。C02 は 32/26/24/18）
    "DVA-C02": {"サービスによる開発": 30, "セキュリティ": 26, "テストとデプロイ": 22, "トラブル": 22},
    "DEA-C01": {"取り込み": 34, "ストア": 26, "運用": 22, "ガバナンス": 18},
    "MLA-C01": {"データ準備": 28, "モデルの開発": 26, "オーケストレーション": 22, "モニタリング": 24},
    # SAP は 2026-11-17 開始の SAP-C03 の 5 ドメイン（2026-11-11 に切り替え。C02 は 組織26/新規29/改善25/移行20）
    "SAP-C02": {"クラウドネイティブ": 25, "ガバナンス": 25, "コスト最適化": 15, "レジリエンス": 15, "運用上の優秀性": 20},
    "DOP-C02": {"SDLC": 22, "構成管理": 17, "耐障害": 15, "モニタリング": 15, "インシデント": 14, "セキュリティ": 17},
    "SOA-C03": {"モニタリング": 22, "信頼性": 22, "デプロイ": 22, "セキュリティ": 16, "ネットワーク": 18},
    "SCS-C03": {"検出": 16, "インシデント": 14, "インフラ": 18, "アイデンティティ": 20, "データ保護": 18, "基礎とガバナンス": 14},
    "AIP-C01": {"基盤モデル": 31, "実装": 26, "安全": 20, "運用": 12, "テスト": 11},
}


def load():
    out = defaultdict(lambda: defaultdict(int))
    for f in sorted((BASE / "資料" / "生成").glob("*_orig*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            out[q["exam"]][q.get("domain", "(未設定)")] += 1
    return out


data = load()
issues = []
for exam in sorted(data):
    doms = data[exam]
    total = sum(doms.values())
    print(f"\n■ {exam}  ({total}問 / ドメイン{len(doms)}種)")
    bp = BLUEPRINT.get(exam)
    matched = set()
    for name, n in sorted(doms.items(), key=lambda x: -x[1]):
        pct = n / total * 100
        target = ""
        if bp:
            hit = [k for k in bp if k in name]
            if hit:
                matched.add(hit[0])
                d = pct - bp[hit[0]]
                target = f"  (公式{bp[hit[0]]}% / 差{d:+.0f}pt)"
                if abs(d) > 10:
                    issues.append(f"{exam} 「{name}」 {pct:.0f}% は公式{bp[hit[0]]}%から{d:+.0f}pt乖離")
            else:
                target = "  ← 公式ドメインに該当なし"
                issues.append(f"{exam} 「{name}」 が公式ドメインと対応しない(表記ゆれか範囲外)")
        print(f"   {name:<40}{n:>4}問 {pct:>5.1f}%{target}")
    if bp:
        missing = set(bp) - matched
        for m in missing:
            issues.append(f"{exam} 公式ドメイン「{m}」({bp[m]}%)に対応する問題が0問")

print("\n" + "=" * 60)
if issues:
    print(f"要対応: {len(issues)}件")
    for i in issues:
        print(f"  - {i}")
else:
    print("ドメイン配分に問題なし")
