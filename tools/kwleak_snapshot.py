# -*- coding: utf-8 -*-
"""キーワード直結の修正作業用: 不変項目のスナップショットを取る / 照合する。

  python tools/kwleak_snapshot.py save     不変項目を保存
  python tools/kwleak_snapshot.py verify   保存内容と照合

不変項目: id / exam / set / type / domain / level / n_correct /
          options[].letter / options[].correct / 正解肢の text
question と誤答肢の text/explanation は変更を許す(この作業の対象)。
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(BASE, "資料", "生成")
SNAP = os.path.join(GEN, "_kwleak_snapshot.json")

FROZEN = ("id", "exam", "set", "type", "domain", "level", "n_correct")


def collect():
    out = {}
    for path in sorted(glob.glob(os.path.join(GEN, "*_orig*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for q in data:
            if not isinstance(q, dict) or "id" not in q:
                continue
            rec = {k: q.get(k) for k in FROZEN}
            rec["file"] = os.path.basename(path)
            rec["options"] = [
                {"letter": o.get("letter"), "correct": o.get("correct"),
                 "text": o.get("text") if o.get("correct") else None}
                for o in q.get("options", [])
            ]
            if q["id"] in out:
                raise SystemExit("duplicate id: %s" % q["id"])
            out[q["id"]] = rec
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    cur = collect()
    if mode == "save":
        json.dump(cur, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("saved %d questions -> %s" % (len(cur), os.path.basename(SNAP)))
        return 0

    old = json.load(open(SNAP, encoding="utf-8"))
    errors = []
    for qid, oq in old.items():
        nq = cur.get(qid)
        if nq is None:
            errors.append("%s: 問題が消えた" % qid)
            continue
        for k in FROZEN:
            if oq.get(k) != nq.get(k):
                errors.append("%s: %s が変わった (%r -> %r)" % (qid, k, oq.get(k), nq.get(k)))
        if len(oq["options"]) != len(nq["options"]):
            errors.append("%s: 選択肢の数が変わった" % qid)
            continue
        for oo, no in zip(oq["options"], nq["options"]):
            for k in ("letter", "correct", "text"):
                if oo.get(k) != no.get(k):
                    errors.append("%s[%s]: 正解肢の %s が変わった" % (qid, oo.get("letter"), k))
    for qid in cur:
        if qid not in old:
            errors.append("%s: 未知の問題が増えた" % qid)

    if errors:
        print("NG: %d件" % len(errors))
        for e in errors[:60]:
            print("  " + e)
        return 1
    print("OK: 不変項目に変化なし (%d問)" % len(cur))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
