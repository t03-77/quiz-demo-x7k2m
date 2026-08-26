# -*- coding: utf-8 -*-
"""解説文と正誤フラグの矛盾を検出する。

「不正解です」で始まる解説なのに correct=true になっていると、学習者は
正しい選択肢を選んだのに解説で否定される。採点自体は通るため自動テストでは
見つからない類のバグなので、テキスト側から突き合わせる。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TARGETS = list((BASE / "資料" / "生成").glob("*_orig*.json"))
TARGETS.append(BASE / "資料" / "変換済み" / "questions_all.json")

issues = []
total = 0
for f in TARGETS:
    data = json.load(open(f, encoding="utf-8"))
    qs = data["questions"] if isinstance(data, dict) else data
    for q in qs:
        if q.get("type") not in (None, "choice"):
            continue
        for o in q.get("options", []):
            ex = (o.get("explanation") or "").lstrip()
            if not ex:
                continue
            total += 1
            says_correct = ex.startswith("正解")
            says_wrong = ex.startswith("不正解")
            if says_correct and not o["correct"]:
                issues.append((q["id"], o["letter"], "解説は正解と述べているがフラグは不正解"))
            elif says_wrong and o["correct"]:
                issues.append((q["id"], o["letter"], "解説は不正解と述べているがフラグは正解"))

print(f"検査した選択肢: {total}個")
print(f"矛盾: {len(issues)}件")
for qid, letter, why in issues[:25]:
    print(f"  {qid} 選択肢{letter}: {why}")
if len(issues) > 25:
    print(f"  …ほか{len(issues)-25}件")
