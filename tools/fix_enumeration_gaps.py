# -*- coding: utf-8 -*-
"""列挙漏れをデータ全体で一括修正する(2026-08-26 実施)。

校閲で見つかる誤りは一貫して「対応するのはA、B、C」型の列挙漏れ。
指摘された箇所だけ直しても同じ誤りが他の問題に残るため、
表現ゆれを吸収する正規表現で全ファイルを走査して直す。
いずれもAWS公式ドキュメントで裏を取った内容。
"""
import json
import re
from pathlib import Path

GEN = Path(__file__).resolve().parent.parent / "資料" / "生成"

# (説明, 検索パターン, 置換後)
FIXES = [
    # 高解像度アラームの期間は 10/20/30 秒 (20秒が抜けていた)
    ("CloudWatch高解像度アラームの期間",
     re.compile(r"10\s*秒または\s*30\s*秒"),
     "10 秒、20 秒、または 30 秒"),
    ("CloudWatch高解像度アラームの期間(別表記)",
     re.compile(r"10\s*秒(?:、|,)\s*30\s*秒"),
     "10 秒、20 秒、30 秒"),

    # Trusted Advisor は6カテゴリ (運用上の優秀性が抜けていた)
    ("TrustedAdvisorのカテゴリ",
     re.compile(r"(コスト最適化(?:、|・)パフォーマンス(?:、|・)セキュリティ(?:、|・)"
                r"フォールトトレランス(?:、|・)サービス(?:クォータ|の制限|制限))(?!(?:、|・)?運用上の優秀性)"),
     r"\1、運用上の優秀性"),

    # Bedrock ガードレールのポリシー (自動推論チェックが抜けていた)
    ("Bedrockガードレールのポリシー",
     re.compile(r"(コンテキストグラウンディングチェック)(?!(?:、|・)?自動推論チェック)"
                r"(?=(の評価結果|を適用|によって|といった|、|。))"),
     r"\1、自動推論チェック"),
]

total = 0
for f in sorted(GEN.glob("*_orig*.json")) + sorted(GEN.glob("mixed_orig*.json")):
    raw = f.read_text(encoding="utf-8")
    qs = json.loads(raw)
    changed = 0
    for q in qs:
        targets = [(q, "explanation")] + [(o, "explanation") for o in q.get("options", [])] \
                  + [(o, "text") for o in q.get("options", [])] + [(q, "question")]
        for obj, key in targets:
            v = obj.get(key)
            if not isinstance(v, str):
                continue
            new = v
            for _, pat, rep in FIXES:
                new = pat.sub(rep, new)
            if new != v:
                obj[key] = new
                changed += 1
    if changed:
        f.write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{f.name}: {changed}箇所")
        total += changed

print(f"\n修正した箇所: {total}")
