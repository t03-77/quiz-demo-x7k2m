# -*- coding: utf-8 -*-
"""AIP-C01 「自前実装型」誤答肢の書き直しパッチを適用する。

誤答肢の text と explanation だけを書き換える。正解肢・question・n_correct 等の
不変項目に触れようとしたら何も書かずに中断する。改行コード(CRLF)と末尾改行の
有無は読み込み時のまま保つ。

使い方: python tools/_aipself_apply.py 資料/生成/_aipself_p01.json [--dry]
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, meta, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "AIP-C01_orig*.json"))):
        raw = Path(f).read_bytes().decode("utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indent = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 2
        meta[f] = {
            "indent": indent,
            "crlf": "\r\n" in raw,
            "tail": raw.endswith("\n") or raw.endswith("\r\n"),
        }
        for q in data:
            index[q["id"]] = (f, q)

    errors, touched = [], set()
    n_text = n_expl = 0
    seen = set()
    for p in patches:
        key = (p["id"], p["letter"])
        if key in seen:
            errors.append(f"{key}: 重複パッチ")
            continue
        seen.add(key)
        if p["id"] not in index:
            errors.append(f"{p['id']}: 該当問題なし")
            continue
        f, q = index[p["id"]]
        opts = [o for o in q["options"] if o["letter"] == p["letter"]]
        if not opts:
            errors.append(f"{p['id']}[{p['letter']}]: 該当選択肢なし")
            continue
        o = opts[0]
        if o["correct"]:
            errors.append(f"{p['id']}[{p['letter']}]: 正解肢は書き換え禁止")
            continue
        if not p.get("text", "").strip() or not p.get("expl", "").strip():
            errors.append(f"{p['id']}[{p['letter']}]: text/expl が空")
            continue
        if not p["expl"].lstrip().startswith("不正解です。"):
            errors.append(f"{p['id']}[{p['letter']}]: 解説は「不正解です。」始まり必須")
            continue
        if p["text"] != o["text"]:
            o["text"] = p["text"]
            n_text += 1
            touched.add(f)
        if p["expl"] != o.get("explanation"):
            o["explanation"] = p["expl"]
            n_expl += 1
            touched.add(f)

    if errors:
        print(f"NG: {len(errors)}件 -> 書き込みなし")
        for e in errors:
            print("  " + e)
        return 1

    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        print("  " + qid + " " + " ".join(
            f"{o['letter']}{'*' if o['correct'] else ''}:{len(o['text'])}"
            for o in q["options"]))

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0

    for f in touched:
        s = json.dumps(files[f], ensure_ascii=False, indent=meta[f]["indent"])
        if meta[f]["tail"]:
            s += "\n"
        if meta[f]["crlf"]:
            s = s.replace("\n", "\r\n")
        Path(f).write_bytes(s.encode("utf-8"))
    print(f"OK: text {n_text}件 / expl {n_expl}件 ({len(touched)}ファイル)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1]))
