# -*- coding: utf-8 -*-
"""SAP-C02 誤答肢の書き直し作業用: 変更前の不変項目をスナップショットする。

書き直してよいのは誤答肢の text と options[].explanation だけ。
id / question / n_correct / letter / correct / 正解肢の text が
作業の前後で完全一致することを後から機械的に確かめるために、
着手前の状態をここに保存しておく。
"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "tools" / "_sap_snapshot.json"


def collect():
    snap = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") != "SAP-C02":
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
    snap = collect()
    OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"snapshot: {len(snap)}問 -> {OUT}")
