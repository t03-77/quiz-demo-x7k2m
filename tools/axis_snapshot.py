# -*- coding: utf-8 -*-
"""選択肢を「軸を共有した集合」に作り替える作業用のスナップショット/照合。

対象資格: MLA-C01 / DVA-C02 / SOA-C03。

この作業では正解肢の text も変えてよい（2×2にするため形を揃える必要があるため）。
そのため text は「変わってはいけない項目」から外し、代わりに変更されたものを
一覧できるようにしてある。絶対に変わってはいけないのは次:

  id / exam / set / type / domain / level / n_correct
  options[].letter / options[].correct / question

使い方:
  python tools/axis_snapshot.py           スナップショット作成
  python tools/axis_snapshot.py --verify  照合（不変項目の差分と、正解肢textの変更一覧）
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "tools" / "_axis_snapshot.json"
EXAMS = ("MLA-C01", "DVA-C02", "SOA-C03")


def collect():
    snap = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") not in EXAMS:
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
                "letters": [o["letter"] for o in q.get("options", [])],
                "correct": [o["correct"] for o in q.get("options", [])],
                # 参考用（変更されたら報告するだけで、エラーにはしない）
                "correct_text": [o["text"] for o in q.get("options", []) if o["correct"]],
            }
    return snap


FIXED = ("exam", "set", "type", "domain", "level", "question",
         "n_correct", "letters", "correct")


def verify():
    old = json.load(open(OUT, encoding="utf-8"))
    new = collect()
    errors = []
    for qid in old:
        if qid not in new:
            errors.append(f"{qid}: 消失")
    for qid in new:
        if qid not in old:
            errors.append(f"{qid}: 新規ID（idは変えてはいけない）")
    changed_correct = []
    for qid in sorted(set(old) & set(new)):
        for k in FIXED:
            if old[qid][k] != new[qid][k]:
                errors.append(f"{qid}: {k} が変更された")
        if old[qid]["correct_text"] != new[qid]["correct_text"]:
            changed_correct.append(qid)

    print(f"照合対象 {len(new)}問")
    if changed_correct:
        print(f"正解肢の text を変更した問題: {len(changed_correct)}問")
        for qid in changed_correct:
            print("  " + qid)
    if errors:
        print(f"NG: 不変項目の差分 {len(errors)}件")
        for e in errors:
            print("  " + e)
        return 1
    print("OK: 不変項目に差分なし")
    return 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        raise SystemExit(verify())
    snap = collect()
    OUT.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"snapshot: {len(snap)}問 -> {OUT}")
