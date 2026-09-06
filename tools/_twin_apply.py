# -*- coding: utf-8 -*-
"""AIP-C01 双子の肢是正パッチを適用する。誤答肢の text / explanation のみ。
使い方: python tools/_twin_apply.py <patch.json> [--dry]
パッチ: [{"id":..,"letter":..,"text":..,"expl":..}]
"""
import json, glob, sys, os
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, index, raws = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "AIP-C01_orig*.json"))):
        if "_bak" in f:
            continue
        raw = Path(f).read_bytes().decode("utf-8")
        raws[f] = raw
        data = json.loads(raw)
        files[f] = data
        for q in data:
            index[q["id"]] = (f, q)

    errors, touched = [], set()
    for p in patches:
        if p["id"] not in index:
            errors.append(f"{p['id']}: なし"); continue
        f, q = index[p["id"]]
        o = next((x for x in q["options"] if x["letter"] == p["letter"]), None)
        if o is None:
            errors.append(f"{p['id']}[{p['letter']}]: 選択肢なし"); continue
        if o.get("correct"):
            errors.append(f"{p['id']}[{p['letter']}]: 正解肢は書き換え禁止"); continue
        if not p.get("expl", "").startswith("不正解です。"):
            errors.append(f"{p['id']}[{p['letter']}]: 解説は「不正解です。」で始める"); continue
        cor = [c["text"] for c in q["options"] if c.get("correct")]
        before = max(SequenceMatcher(None, c, o["text"]).ratio() for c in cor)
        after = max(SequenceMatcher(None, c, p["text"]).ratio() for c in cor)
        lens = [(x["letter"], len(x["text"]), x.get("correct")) for x in q["options"]]
        print(f'{p["id"]}[{p["letter"]}] sim {before:.3f} -> {after:.3f} '
              f'len {len(o["text"])}->{len(p["text"])} expl {len(p["expl"])}字 '
              f'others={[(l,n) for l,n,c in lens if l!=p["letter"]]}')
        o["text"] = p["text"]
        o["explanation"] = p["expl"]
        touched.add(f)

    if errors:
        print("NG: 書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1
    if "--dry" in sys.argv:
        print("(dry)")
        return 0
    for f in touched:
        s = json.dumps(files[f], ensure_ascii=False, indent=2)
        if raws[f].endswith("\n"):
            s += "\n"
        Path(f).write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
    print(f"OK: {len(patches)}件 / {len(touched)}ファイル")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
