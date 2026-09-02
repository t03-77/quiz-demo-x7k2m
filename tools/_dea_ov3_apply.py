# -*- coding: utf-8 -*-
"""DEA-C01 誤答肢の書き直しパッチを適用する(肢どうしの語の重なり改善 第3弾)。"""
import json, glob, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
IMM = ("id", "exam", "set", "type", "domain", "level", "n_correct", "question")


def fingerprint(data):
    r = {}
    for q in data:
        if q.get("exam") != "DEA-C01":
            continue
        r[q["id"]] = {k: q.get(k) for k in IMM} | {
            "opts": [(o.get("letter"), bool(o.get("correct")),
                      o["text"] if o.get("correct") else None,
                      o.get("explanation") if o.get("correct") else None)
                     for o in q.get("options") or []]
        }
    return r


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, index, before = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "DEA-C01_orig*.json"))):
        if "_bak" in f:
            continue
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        files[f] = data
        before[f] = fingerprint(data)
        for q in data:
            if q.get("exam") == "DEA-C01":
                index[q["id"]] = (f, q)

    errors, touched, seen = [], set(), set()
    n_t = n_e = 0
    for p in patches:
        key = (p["id"], p["letter"])
        if key in seen:
            errors.append(f"{key}: 重複パッチ"); continue
        seen.add(key)
        if p["id"] not in index:
            errors.append(f"{p['id']}: 該当問題なし"); continue
        f, q = index[p["id"]]
        opts = [o for o in q["options"] if o["letter"] == p["letter"]]
        if not opts:
            errors.append(f"{key}: 該当選択肢なし"); continue
        o = opts[0]
        if o["correct"]:
            errors.append(f"{key}: 正解肢は書き換え禁止"); continue
        if not p["text"].strip() or not p["expl"].lstrip().startswith("不正解です。"):
            errors.append(f"{key}: text 空 または expl の書き出しが不正"); continue
        if o["text"] != p["text"]:
            o["text"] = p["text"]; n_t += 1; touched.add(f)
        if (o.get("explanation") or "") != p["expl"]:
            o["explanation"] = p["expl"]; n_e += 1; touched.add(f)

    for f in files:
        if before[f] != fingerprint(files[f]):
            errors.append(f"{f}: 不変項目が変化した")

    if errors:
        print("NG: 書き込みなし")
        for e in errors:
            print("  " + e)
        return 1

    if "--dry" not in sys.argv:
        for f in sorted(touched):
            Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(("(dry) " if "--dry" in sys.argv else "") +
          f"OK: text {n_t}件 / expl {n_e}件 / {len(touched)}ファイル")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
