# -*- coding: utf-8 -*-
"""CLF-C02 の誤答肢そろえ作業用: 変更前の不変項目をスナップショットする。

この作業で書き直してよいのは 誤答肢の text と options[].explanation だけ。
id / exam / set / type / domain / level / question / n_correct / letter /
correct / 正解肢の text が作業の前後で完全一致することを後から機械的に
確かめるため、着手前の状態をここに保存しておく。

question は基礎資格として先日調整したばかりで、今回は一切触らない。
そのため scs 版とは違い、question も「完全一致」の対象にする。
"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXAM = "CLF-C02"
OUT = BASE / "tools" / "_clf_snapshot.json"


def collect():
    snap = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") != EXAM:
                continue
            snap[q["id"]] = {
                "file": Path(f).name,
                "exam": q["exam"],
                "set": q.get("set"),
                "type": q.get("type", "choice"),
                "domain": q.get("domain"),
                "level": q.get("level"),
                "question": q["question"],
                "n_correct": q.get("n_correct"),
                "options": [
                    {"letter": o["letter"], "correct": o["correct"],
                     "text": o["text"] if o["correct"] else None}
                    for o in q.get("options", [])
                ],
            }
    return snap


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit(f"既にスナップショットがあります: {OUT}\n"
                         "作業前の状態を失うため上書きしません。")
    snap = collect()
    OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"snapshot: {len(snap)}問 -> {OUT}")
