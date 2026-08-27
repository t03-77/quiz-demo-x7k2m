# -*- coding: utf-8 -*-
"""誤答肢の書き直しにあわせて解説へ足した一文のうち、重複しているものを外す。

選択肢を具体化した際、その要素への評価を解説の末尾へ補ったが、
元の解説がすでに同じ内容を述べている箇所がある。同じことを二度書くと
解説が冗長になるため、既存の本文と語がほぼ重なる追記だけを取り除く。
"""
import json
import glob
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
THRESHOLD = 0.5


def kw(s):
    return set(re.findall(r"[A-Za-z][A-Za-z0-9]{2,}|[ぁ-んァ-ヶ一-龠]{3,}", s))


def main():
    appended = {}
    for f in sorted(glob.glob(str(GEN / "_dop_patch_*.json"))):
        for p in json.load(open(f, encoding="utf-8")):
            if "append" in p:
                appended[(p["id"], p["letter"])] = p["append"]

    removed = 0
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        lines = raw.split("\n")
        indent = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        changed = False
        for q in data:
            if q.get("exam") != "DOP-C02":
                continue
            for o in q.get("options", []):
                add = appended.get((q["id"], o["letter"]))
                ex = o.get("explanation") or ""
                if not add or not ex.endswith(add):
                    continue
                rest = ex[: -len(add)]
                k = kw(add)
                if not k:
                    continue
                if len(k & kw(rest)) / len(k) >= THRESHOLD:
                    o["explanation"] = rest.rstrip()
                    changed = True
                    removed += 1
                    print(f"  {q['id']}[{o['letter']}] 重複していた追記を削除")
        if changed:
            Path(f).write_text(json.dumps(data, ensure_ascii=False, indent=indent or 1),
                               encoding="utf-8")
    print(f"削除した追記: {removed}件")


if __name__ == "__main__":
    main()
