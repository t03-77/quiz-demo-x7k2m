# -*- coding: utf-8 -*-
"""MLA-C01 精読(事実誤りの是正)用パッチ適用。

mla_apply_patch.py との違いは 2 点だけ。

1. **保存形式を推測せず、無改変ラウンドトリップがバイト一致することを確認してから書く。**
   MLA の 6 ファイルは indent=2 / CRLF / 末尾改行あり だが、
   mla_apply_patch.py は末尾改行を落としてしまう。
2. 正解肢の explanation も直せる(事実誤りは正解肢の解説にも出るため)。
   ただし **正解肢の text への書き込みは検出したら 1 件も書かずに中断**する。
   letter / correct / question / n_correct なども一切触らない。

パッチ1件の形式:
  {"id": "...", "letter": "B",
   "sub": ["置換前", "置換後"],      # explanation の部分置換(1箇所ちょうど)
   "expl": "差し替える解説全文",      # または全文差し替え
   "text_sub": ["置換前", "置換後"]}  # 誤答肢の text の部分置換(任意)

使い方: python -X utf8 tools/_mla_seidoku_apply.py <patch.json> [--dry]
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
FILES = [
    "MLA-C01_orig.json",
    "MLA-C01_orig_b2.json",
    "MLA-C01_orig_b3.json",
    "MLA-C01_orig_b4.json",
    "MLA-C01_orig_gap1.json",
    "MLA-C01_orig_topic1.json",
]


def detect(raw: bytes):
    """元ファイルとバイト一致する (indent, newline, trailing) を求める。"""
    data = json.loads(raw.decode("utf-8"))
    for indent in (1, 2, 4):
        for nl in ("\r\n", "\n"):
            for tr in (True, False):
                s = json.dumps(data, ensure_ascii=False, indent=indent).replace("\n", nl)
                if tr:
                    s += nl
                if s.encode("utf-8") == raw:
                    return data, (indent, nl, tr)
    return data, None


def dump(data, fmt):
    indent, nl, tr = fmt
    s = json.dumps(data, ensure_ascii=False, indent=indent).replace("\n", nl)
    if tr:
        s += nl
    return s.encode("utf-8")


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, fmts, index = {}, {}, {}
    errors = []
    for name in FILES:
        p = GEN / name
        raw = p.read_bytes()
        data, fmt = detect(raw)
        if fmt is None:
            errors.append(f"{name}: 無改変ラウンドトリップがバイト一致しない。中断")
            continue
        files[name] = data
        fmts[name] = fmt
        for q in data:
            if q.get("exam") == "MLA-C01":
                index[q["id"]] = (name, q)
    if errors:
        print("NG:", *errors, sep="\n  ")
        return 1

    touched = set()
    n_text = n_expl = 0
    seen = set()
    for pa in patches:
        key = (pa["id"], pa["letter"])
        if key in seen:
            errors.append(f"{key}: 同じ選択肢へのパッチが重複")
            continue
        seen.add(key)
        if pa["id"] not in index:
            errors.append(f"{pa['id']}: 該当問題なし")
            continue
        name, q = index[pa["id"]]
        opts = [o for o in q.get("options", []) if o["letter"] == pa["letter"]]
        if not opts:
            errors.append(f"{pa['id']}[{pa['letter']}]: 該当選択肢なし")
            continue
        o = opts[0]
        if "text_sub" in pa:
            if o["correct"]:
                errors.append(f"{pa['id']}[{pa['letter']}]: 正解肢の text は書き換え禁止")
                continue
            old, new = pa["text_sub"]
            if o["text"].count(old) != 1:
                errors.append(f"{pa['id']}[{pa['letter']}]: text 置換対象が{o['text'].count(old)}箇所")
                continue
            o["text"] = o["text"].replace(old, new)
            n_text += 1
            touched.add(name)
        ex = o.get("explanation") or ""
        new_ex = None
        if "expl" in pa:
            new_ex = pa["expl"]
        elif "sub" in pa:
            old, new = pa["sub"]
            if ex.count(old) != 1:
                errors.append(f"{pa['id']}[{pa['letter']}]: 解説の置換対象が{ex.count(old)}箇所 -> {old[:30]}")
                continue
            new_ex = ex.replace(old, new)
        if new_ex is not None and new_ex != ex:
            head = "正解です" if o["correct"] else "不正解です"
            if not new_ex.lstrip().startswith(head):
                errors.append(f"{pa['id']}[{pa['letter']}]: 解説は「{head}。」で始める必要がある")
                continue
            o["explanation"] = new_ex
            n_expl += 1
            touched.add(name)

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    print(f"対象: text {n_text}件 / 解説 {n_expl}件 ({len(touched)}ファイル)")
    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0
    for name in sorted(touched):
        (GEN / name).write_bytes(dump(files[name], fmts[name]))
    print("OK: 書き込み完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
