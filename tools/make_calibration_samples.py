# -*- coding: utf-8 -*-
"""公式模試から「お手本」を抽出する。

問題文だけでなく**公式の解説をそのまま**入れるのが要点。
解説の分量・書き出し・根拠の示し方まで含めて基準を渡さないと、
生成される解説が公式の半分以下の長さになる(実測: 公式229字 / 生成97字)。
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "資料" / "変換済み" / "questions_all.json"
OUT_DIR = BASE / "資料" / "校正サンプル"
PER_EXAM = 8

d = json.load(open(SRC, encoding="utf-8"))
qs = [q for q in d["questions"]
      if q["set"] in ("exam", "pretest") and q["type"] == "choice"]

by_exam = {}
for q in qs:
    by_exam.setdefault(q["exam"], []).append(q)

OUT_DIR.mkdir(exist_ok=True)
for exam, items in by_exam.items():
    # 解説が充実していて、選択肢も揃っているものを基準として選ぶ
    scored = sorted(
        items,
        key=lambda q: -(sum(len(o.get("explanation", "")) for o in q["options"])
                        + len(q["question"])),
    )
    picks = scored[:PER_EXAM]

    L = [f"# {exam} 公式模試のお手本（これと同じ水準で作ること）\n",
         "以下はAWS公式の模擬試験問題そのものです。**問題文の長さ・シナリオの作り方・",
         "誤答選択肢の作り込み・解説の分量と書き方**を、この水準に合わせてください。",
         "特に解説は、単に正誤を述べるだけでなく「なぜそうなるのか」「なぜ他は違うのか」を",
         "具体的に説明し、参照すべきAWSドキュメントの名称に触れています。\n"]
    for q in picks:
        L.append(f"---\n\n## 例: {q['id']}")
        L.append(f"\n**問題文**（{len(q['question'])}字）\n")
        L.append(q["question"])
        L.append(f"\n**選択肢と解説**\n")
        for o in q["options"]:
            mark = " ← 正解" if o["correct"] else ""
            ex = re.sub(r"\n{2,}", "\n", o.get("explanation", "")).strip()
            L.append(f"- **{o['letter']}. {o['text']}**{mark}")
            L.append(f"  - 解説（{len(ex)}字）: {ex}")
        L.append("")

    avg_q = sum(len(q["question"]) for q in picks) // len(picks)
    avg_e = sum(len(o.get("explanation", "")) for q in picks for o in q["options"]) \
        // sum(len(q["options"]) for q in picks)
    L.append(f"---\n\n## この試験の基準値\n")
    L.append(f"- 問題文: 平均 {avg_q} 字")
    L.append(f"- 選択肢ごとの解説: 平均 {avg_e} 字")
    L.append(f"- 解説は「正解です。/不正解です。」で始め、根拠を述べ、"
             f"関連するAWSサービス・機能の正式名称に触れる")

    (OUT_DIR / f"{exam}.md").write_text("\n".join(L), encoding="utf-8")
    print(f"{exam}: {len(picks)}問 / 問題文平均{avg_q}字 / 解説平均{avg_e}字")
