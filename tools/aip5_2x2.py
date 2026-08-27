# -*- coding: utf-8 -*-
"""AIP-C01 の4肢を「(軸1)×(軸2)」の2×2構造へ書き換える。

この作業に限り正解肢の text も変更してよい。ただし取り違えを防ぐため、
正解肢を書き換えるパッチには "correct": true を明示させ、
実データの correct と一致しない場合は1件も書かずに中断する。

パッチ1件の形式:
  {"id": "...", "letter": "A", "correct": true, "text": "...", "expl": "..."}

使い方: python tools/aip5_2x2.py 資料/生成/_aip5_2x2_01.json [--dry]
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, indents, index = {}, {}, {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        files[f] = json.loads(raw)
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in files[f]:
            if q.get("exam") == "AIP-C01" and q.get("set") == "orig":
                index[q["id"]] = (f, q)

    errs, seen = [], set()
    for p in patches:
        key = (p["id"], p["letter"])
        if key in seen:
            errs.append(f"{key}: 重複"); continue
        seen.add(key)
        if p["id"] not in index:
            errs.append(f"{p['id']}: 該当なし"); continue
        q = index[p["id"]][1]
        o = [x for x in q["options"] if x["letter"] == p["letter"]]
        if not o:
            errs.append(f"{p['id']}[{p['letter']}]: 該当選択肢なし"); continue
        o = o[0]
        if bool(p.get("correct")) != bool(o["correct"]):
            errs.append(f"{p['id']}[{p['letter']}]: correct の宣言が実データと違う")
            continue
        if not p.get("text", "").strip():
            errs.append(f"{p['id']}[{p['letter']}]: text が空"); continue
        head = "正解です。" if o["correct"] else "不正解です。"
        if "expl" in p and not p["expl"].lstrip().startswith(head):
            errs.append(f"{p['id']}[{p['letter']}]: 解説は「{head}」で始める必要がある")
    # 各問について、パッチ適用後も正解が1つ残ることを確認
    for qid in {p["id"] for p in patches}:
        if qid in index:
            q = index[qid][1]
            if sum(1 for x in q["options"] if x["correct"]) != q.get("n_correct"):
                errs.append(f"{qid}: 正解数が n_correct と一致しない")
    if errs:
        print(f"事前検査 NG {len(errs)}件。1件も書き込みません。")
        for e in errs:
            print("  " + e)
        return 1

    dirty, nt, ne = set(), 0, 0
    for p in patches:
        f, q = index[p["id"]]
        o = [x for x in q["options"] if x["letter"] == p["letter"]][0]
        if o["text"] != p["text"]:
            o["text"] = p["text"]; nt += 1; dirty.add(f)
        if "expl" in p and o.get("explanation") != p["expl"]:
            o["explanation"] = p["expl"]; ne += 1; dirty.add(f)
    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0
    for f in sorted(dirty):
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                           encoding="utf-8")
    print(f"OK: text {nt}件 / 解説 {ne}件 を更新 ({len(dirty)}ファイル, {len({p['id'] for p in patches})}問)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
