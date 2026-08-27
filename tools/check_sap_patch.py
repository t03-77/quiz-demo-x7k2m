# -*- coding: utf-8 -*-
"""SAP-C02 パッチの文字数をレンジ (正解 200-320 / 誤答 150-260) で検査する。"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def load_correct_map():
    m = {}
    for f in sorted(GEN.glob("SAP-C02_orig*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            m[q["id"]] = {o["letter"]: o["correct"] for o in q["options"]}
    return m


def main(patch_path):
    patch = json.load(open(patch_path, encoding="utf-8-sig"))
    cm = load_correct_map()
    bad = 0
    for qid in sorted(patch):
        for letter in sorted(patch[qid]):
            text = patch[qid][letter]
            n = len(text)
            correct = cm[qid][letter]
            lo, hi = (200, 320) if correct else (150, 260)
            ok = lo <= n <= hi
            head_ok = text.startswith("正解です。" if correct else "不正解です。")
            if not ok or not head_ok:
                bad += 1
                print(f"{qid} {letter} {'O' if correct else 'X'} {n}"
                      f"{'' if ok else ('  SHORT' if n < lo else '  LONG')}"
                      f"{'' if head_ok else '  BAD-PREFIX'}")
    print(f"NG={bad} / total={sum(len(v) for v in patch.values())}")


if __name__ == "__main__":
    main(sys.argv[1])
