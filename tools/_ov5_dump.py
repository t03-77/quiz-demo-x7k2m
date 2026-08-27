# -*- coding: utf-8 -*-
"""指定IDの問題を読みやすい形で出す(重なり改善作業用)。
使い方: python tools/_ov5_dump.py ID [ID ...]
"""
import glob
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def index():
    idx = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("set") == "orig":
                idx[q["id"]] = (Path(f).name, q)
    return idx


if __name__ == "__main__":
    idx = index()
    for qid in [a for a in sys.argv[1:] if not a.startswith("--")]:
        f, q = idx[qid]
        print("=" * 70)
        print(f"{qid}  [{f}] domain={q.get('domain')} level={q.get('level')} n_correct={q.get('n_correct')}")
        print("Q: " + q["question"])
        for o in q["options"]:
            mark = "★正解" if o["correct"] else "  誤答"
            print(f"{mark} {o['letter']}. {o['text']}")
            ex = o.get("explanation") or ""
            if "--noexpl" in sys.argv:
                continue
            if "--short" in sys.argv:
                ex = ex[:110] + ("…" if len(ex) > 110 else "")
            print(f"      expl({len(o.get('explanation') or '')}): {ex}")
        print()
