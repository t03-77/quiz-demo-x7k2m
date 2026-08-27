# -*- coding: utf-8 -*-
"""AIP-C01 の「1正解5肢」から誤答を1つ削って4肢にする。

安全装置:
  - 正解肢を削ろうとしたら1件も書かずに中断
  - 5肢でない / n_correct が 1 でない場合も中断
  - head（削除対象テキストの先頭）が一致しない場合も中断
  - 削除後に正解が1つ残っていない場合も中断
  - 解説が削除する選択肢を letter で参照していないか確認
  - 10問処理するごとに保存

使い方: python tools/aip5_trim.py 資料/生成/_aip5_delete_map_01.json
"""
import json
import glob
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LETTERS = "ABCDEFGH"
REF = re.compile(r"選択肢\s*[A-F]|[（(]\s*[A-F]\s*[）)]")


def main(map_path):
    dmap = json.load(open(map_path, encoding="utf-8"))
    files, indents, index = {}, {}, {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if q.get("exam") == "AIP-C01" and q.get("set") == "orig":
                index[q["id"]] = (f, q)

    errs = []
    for qid, spec in dmap.items():
        if qid not in index:
            errs.append(f"{qid}: 該当なし"); continue
        q = index[qid][1]
        if q.get("n_correct") != 1:
            errs.append(f"{qid}: n_correct != 1"); continue
        if len(q["options"]) != 5:
            errs.append(f"{qid}: 選択肢が {len(q['options'])} 個"); continue
        tgt = [o for o in q["options"] if o["letter"] == spec["letter"]]
        if not tgt:
            errs.append(f"{qid}: letter {spec['letter']} なし"); continue
        o = tgt[0]
        if o["correct"]:
            errs.append(f"{qid}[{spec['letter']}]: 正解肢を削除しようとしている"); continue
        if not o["text"].startswith(spec["head"]):
            errs.append(f"{qid}[{spec['letter']}]: head 不一致 -> {o['text'][:40]}"); continue
        rest = [x for x in q["options"] if x["letter"] != spec["letter"]]
        if sum(1 for x in rest if x["correct"]) != 1:
            errs.append(f"{qid}: 削除後の正解数が 1 でない"); continue
        for x in rest:
            if REF.search(x.get("explanation") or ""):
                errs.append(f"{qid}[{x['letter']}]: 解説が letter を参照している")
    if errs:
        print(f"事前検査 NG {len(errs)}件。1件も書き込みません。")
        for e in errs:
            print("  " + e)
        return 1
    print(f"事前検査 OK: {len(dmap)}問")

    dirty, done = set(), 0
    for qid in dmap:
        spec = dmap[qid]
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] != spec["letter"]]
        for i, o in enumerate(opts):
            o["letter"] = LETTERS[i]
        q["options"] = opts
        dirty.add(f)
        done += 1
        if done % 10 == 0:
            for x in sorted(dirty):
                Path(x).write_text(json.dumps(files[x], ensure_ascii=False, indent=indents[x] or 1),
                                   encoding="utf-8")
            dirty.clear()
            print(f"  保存: {done}問まで")
    for x in sorted(dirty):
        Path(x).write_text(json.dumps(files[x], ensure_ascii=False, indent=indents[x] or 1),
                           encoding="utf-8")
    print(f"完了: {done}問を4肢に変更")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
