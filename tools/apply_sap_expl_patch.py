# -*- coding: utf-8 -*-
"""SAP-C02 の options[].explanation だけを差し替えるパッチ適用スクリプト。

使い方: python tools/apply_sap_expl_patch.py <patch.json>

パッチ形式: {"SAP-C02_orig_041": {"A": "解説…", "B": "解説…"}, ...}
explanation 以外のフィールドには一切触れない。
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
FILES = sorted(GEN.glob("SAP-C02_orig*.json"))


def main(patch_path):
    patch = json.load(open(patch_path, encoding="utf-8-sig"))
    remaining = {k: dict(v) for k, v in patch.items()}
    applied = 0
    for f in FILES:
        data = json.load(open(f, encoding="utf-8"))
        dirty = False
        for q in data:
            qp = remaining.get(q["id"])
            if not qp:
                continue
            for o in q["options"]:
                if o["letter"] in qp:
                    new = qp.pop(o["letter"])
                    if o.get("explanation") != new:
                        o["explanation"] = new
                        dirty = True
                    applied += 1
            if not qp:
                remaining.pop(q["id"])
        if dirty:
            with open(f, "w", encoding="utf-8", newline="\r\n") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            print(f"updated {f.name}")
    if remaining:
        print("WARN: 未適用の項目があります ->", json.dumps(
            {k: sorted(v.keys()) for k, v in remaining.items()}, ensure_ascii=False))
    print(f"applied {applied} explanations")


if __name__ == "__main__":
    main(sys.argv[1])
