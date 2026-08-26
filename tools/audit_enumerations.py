# -*- coding: utf-8 -*-
"""「対応するのはA、B、Cです」型の列挙・限定記述を洗い出す。

DEA-C01_orig_031 では「S3イベント通知の送信先はSNS/SQS/Lambda」と書き、
EventBridge を落としていた。この手の網羅漏れは正解と矛盾しても
自動テストでは検出できないため、人が確認する候補としてリスト化する。
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# 列挙・限定を宣言している文を拾う
SENT = re.compile(r"[^。]*?(?:"
                  r"(?:送信先|ターゲット|宛先|出力先|保存先|対象|オプション|方式|タイプ|種類|形式)は[^。]*?(?:のみ|だけ|です|であり|に限)"
                  r"|(?:サポート|対応|利用|使用|指定|選択)(?:される|できる|しているの)は[^。]*?(?:のみ|だけ|です|であり)"
                  r"|[０-９0-9]\s*(?:種類|つ)(?:のみ|だけ|です|であり)"
                  r")[^。]*。")


def iter_texts():
    for f in sorted((BASE / "資料" / "生成").glob("*_orig*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            for o in q.get("options", []):
                yield q["id"], o["letter"], o.get("explanation", "")


hits = []
n = 0
for qid, letter, ex in iter_texts():
    n += 1
    for m in SENT.finditer(ex):
        s = m.group(0).strip()
        # 列挙(読点で3語以上)か、限定表現を含むものだけを対象にする
        if s.count("、") >= 2 or "のみ" in s or "だけ" in s:
            hits.append((qid, letter, s))
            break

print(f"検査した選択肢: {n}個")
print(f"列挙・限定を断定している記述: {len(hits)}件\n")
for qid, letter, s in hits:
    print(f"{qid} [{letter}]")
    print(f"   {s[:150]}")
