# -*- coding: utf-8 -*-
"""正解肢の text を書き換える(2x2マトリクス化のため)。1問ずつ根拠を確認して使う。

any_apply_patch.py は正解肢への書き込みを一律で拒否するため、
「正解であることは変えず、表現を2要素に分解する」目的の変更だけを
ここで扱う。取り違え防止のため **変更前の text を old として必ず書かせ、
完全一致しなければ1件も書き込まない**。

パッチ1件の形式:
  {"id": "...", "letter": "A", "old": "変更前の全文", "text": "変更後の全文",
   "expl": "差し替える解説全文(省略可)"}

使い方: python tools/_ov5_apply_correct.py <パッチ.json> [--dry]
"""
import glob
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
ALLOWED = {"DEA-C01", "SAA-C03", "SAP-C02", "SCS-C03", "DOP-C02"}


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, indents, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            index[q["id"]] = (f, q)

    errors, touched = [], set()
    n_text = n_expl = 0
    for p in patches:
        qid, letter = p["id"], p["letter"]
        if qid not in index:
            errors.append(f"{qid}: 該当問題なし")
            continue
        f, q = index[qid]
        if q.get("exam") not in ALLOWED:
            errors.append(f"{qid}: 担当外の資格 {q.get('exam')}")
            continue
        opts = [o for o in q["options"] if o["letter"] == letter]
        if not opts:
            errors.append(f"{qid}[{letter}]: 該当選択肢なし")
            continue
        o = opts[0]
        if not o["correct"]:
            errors.append(f"{qid}[{letter}]: 正解肢ではない。誤答は any_apply_patch.py を使うこと")
            continue
        if o["text"] != p["old"]:
            errors.append(f"{qid}[{letter}]: old が現在の text と一致しない")
            continue
        if not p["text"].strip():
            errors.append(f"{qid}[{letter}]: text が空")
            continue
        if "expl" in p and not p["expl"].lstrip().startswith("正解"):
            errors.append(f"{qid}[{letter}]: 正解の解説は「正解です。」で始める必要がある")
            continue
        p["_o"] = o
        p["_f"] = f

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    for p in patches:
        o, f = p["_o"], p["_f"]
        if o["text"] != p["text"]:
            o["text"] = p["text"]
            n_text += 1
            touched.add(f)
        if "expl" in p and p["expl"] != o.get("explanation"):
            o["explanation"] = p["expl"]
            n_expl += 1
            touched.add(f)

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0
    for f in touched:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                           encoding="utf-8")
    print(f"OK: 正解肢テキスト {n_text}件 / 解説 {n_expl}件 を更新 ({len(touched)}ファイル)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
