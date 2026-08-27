# -*- coding: utf-8 -*-
"""1正解5肢の問題から誤答肢を1つ削って1正解4肢にする。

公式問題には「1正解5肢」が0問しかない。この形は誤答の4つ目が
水増しになりやすいため、価値の最も低い誤答を1つ落として4肢にそろえる。

安全装置:
  - 削除対象が正解肢だった場合は1件も書かずに中断する
  - 削除後に正解が1つ残っていない場合も中断する
  - 対象の text が想定と違う場合も中断する
  - 10問処理するごとにファイルへ保存する
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MAP = BASE / "資料" / "生成" / "_5opt_delete_map.json"
LETTERS = "ABCDEFGH"


def load_files():
    files = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, list):
            files[f] = d
    return files


def save(files, dirty):
    for f in sorted(dirty):
        Path(f).write_text(
            json.dumps(files[f], ensure_ascii=False, indent=1), encoding="utf-8")
    dirty.clear()


def main():
    dmap = json.load(open(MAP, encoding="utf-8"))
    files = load_files()
    index = {}
    for f, d in files.items():
        for q in d:
            if q.get("id") in dmap:
                index[q["id"]] = (f, q)

    missing = sorted(set(dmap) - set(index))
    if missing:
        print("対象が見つからない:", missing)
        return 1

    # --- 事前検査（1件も書かずに全件チェック）---
    errs = []
    for qid, spec in dmap.items():
        f, q = index[qid]
        if q.get("n_correct") != 1:
            errs.append(f"{qid}: n_correct が 1 でない")
            continue
        if len(q["options"]) != 5:
            errs.append(f"{qid}: 選択肢が5つでない ({len(q['options'])})")
            continue
        tgt = [o for o in q["options"] if o["letter"] == spec["letter"]]
        if not tgt:
            errs.append(f"{qid}: letter {spec['letter']} が無い")
            continue
        o = tgt[0]
        if o["correct"]:
            errs.append(f"{qid}[{spec['letter']}]: 正解肢を削除しようとしている")
            continue
        if not o["text"].startswith(spec["head"]):
            errs.append(f"{qid}[{spec['letter']}]: text が想定と違う -> {o['text'][:40]}")
    if errs:
        print(f"事前検査で {len(errs)} 件の問題。1件も書き込まずに中断します。")
        for e in errs:
            print("  " + e)
        return 1
    print(f"事前検査 OK: {len(dmap)}問")

    # --- 適用（10問ごとに保存）---
    dirty = set()
    done = 0
    for qid in sorted(dmap):
        spec = dmap[qid]
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] != spec["letter"]]
        assert len(opts) == 4, qid
        assert sum(1 for o in opts if o["correct"]) == 1, qid
        for i, o in enumerate(opts):
            o["letter"] = LETTERS[i]
        q["options"] = opts
        dirty.add(f)
        done += 1
        if done % 10 == 0:
            save(files, dirty)
            print(f"  保存: {done}問まで")
    save(files, dirty)
    print(f"完了: {done}問を4肢に変更")
    return 0


if __name__ == "__main__":
    sys.exit(main())
