# -*- coding: utf-8 -*-
"""SAA-C03/AIF-C01 の複文率調整パッチを適用する。

正解肢の text も書き換える作業なので既存の apply_patch の安全装置は使えない。
代わりに以下を強制する:
  - 正解肢を書き換えるときは "allow_correct": true を明示する
  - "want" で目標の文数(2=2文以上 / 1=1文)を宣言し、一致しなければ1件も書かない
  - 書き込みは対象2資格のファイルのみ。書式は既存ファイルから推定した値を使う
使い方: python tools/_fukubun_apply.py 資料/生成/_patch.json [--dry]
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fukubun_lib import load, save, sent, overlap

EXAMS = ("SAA-C03", "AIF-C01")


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, index = {}, {}
    for ex in EXAMS:
        fl, ix = load(ex)
        files.update(fl)
        index.update(ix)
    before = {qid: (overlap(q), [len(o["text"]) for o in q["options"]]) for qid, (f, q) in index.items()}
    errors, touched, seen = [], set(), set()
    n_text = 0
    for p in patches:
        qid, letter = p["id"], p["letter"]
        if qid not in index:
            errors.append("%s: 該当なし" % qid); continue
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] == letter]
        if not opts:
            errors.append("%s[%s]: 選択肢なし" % (qid, letter)); continue
        o = opts[0]
        if (qid, letter) in seen:
            errors.append("%s[%s]: 重複パッチ" % (qid, letter)); continue
        seen.add((qid, letter))
        t = (p.get("text") or "").strip()
        if not t:
            errors.append("%s[%s]: text が空" % (qid, letter)); continue
        want = p["want"]
        n = len(sent(t))
        if want == 2 and n < 2:
            errors.append("%s[%s]: 2文以上にならない(%d文)" % (qid, letter, n)); continue
        if want == 1 and n != 1:
            errors.append("%s[%s]: 1文になっていない(%d文)" % (qid, letter, n)); continue
        if o["correct"] and not p.get("allow_correct"):
            errors.append("%s[%s]: 正解肢の書き換えには allow_correct が要る" % (qid, letter)); continue
        if not o["correct"] and p.get("allow_correct"):
            errors.append("%s[%s]: 誤答肢に allow_correct(取り違え?)" % (qid, letter)); continue
        if t == o["text"]:
            errors.append("%s[%s]: 変化なし" % (qid, letter)); continue
        o["text"] = t; n_text += 1; touched.add(f)
    if errors:
        print("NG: %d件のため何も書き込みませんでした" % len(errors))
        for e in errors:
            print("  " + e)
        return 1
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wr = [o for o in q["options"] if not o["correct"]]
        mx = max(len(o["text"]) for o in q["options"])
        cls = "hi" if (max(len(o["text"]) for o in cor) == mx and max(len(o["text"]) for o in wr) != mx) else \
              ("lo" if (max(len(o["text"]) for o in wr) == mx and max(len(o["text"]) for o in cor) != mx) else "same")
        n2 = sum(1 for o in q["options"] if len(sent(o["text"])) >= 2)
        ob, lb = before[qid]
        print("  %s 2文%d/%d 長さ%s->%s [%s] 重なり%.3f->%.3f" % (
            qid, n2, len(q["options"]), lb, [len(o["text"]) for o in q["options"]], cls, ob, overlap(q)))
    if "--dry" in sys.argv:
        print("(--dry) 書き込みなし"); return 0
    save(files, touched)
    print("OK: text %d件 (%dファイル)" % (n_text, len(touched)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
