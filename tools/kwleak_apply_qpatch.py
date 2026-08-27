# -*- coding: utf-8 -*-
"""問題文 (question) だけを差し替える。既存のインデント幅を保って書き戻す。

  python tools/kwleak_apply_qpatch.py <patch.json>

patch.json は [{"id": "...", "old": "置換前の部分文字列", "new": "置換後"}] または
[{"id": "...", "question": "新しい問題文全文"}] の配列。
old を使う場合、その文字列がちょうど1箇所にないと1件も書き込まずに中断する。
question 以外のフィールドには一切触れない。
"""
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, indents, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            continue
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if isinstance(q, dict) and q.get("id"):
                index[q["id"]] = (f, q)

    errors, touched, plan = [], set(), []
    for p in patches:
        if p["id"] not in index:
            errors.append("%s: 該当問題なし" % p["id"])
            continue
        f, q = index[p["id"]]
        old_q = q["question"]
        if "question" in p:
            new_q = p["question"]
        else:
            if old_q.count(p["old"]) != 1:
                errors.append("%s: 置換対象が%d箇所 -> %s" % (p["id"], old_q.count(p["old"]), p["old"][:24]))
                continue
            new_q = old_q.replace(p["old"], p["new"])
        if new_q == old_q:
            errors.append("%s: 変化なし" % p["id"])
            continue
        plan.append((f, q, new_q, len(old_q), len(new_q)))
        touched.add(f)

    if errors:
        print("NG: %d件のため何も書き込みませんでした" % len(errors))
        for e in errors:
            print("  " + e)
        return 1

    for f, q, new_q, a, b in plan:
        q["question"] = new_q
        print("  %s: %d -> %d 字" % (q["id"], a, b))
    for f in touched:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1), encoding="utf-8")
    print("OK: 問題文 %d件 を更新 (%dファイル)" % (len(plan), len(touched)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
