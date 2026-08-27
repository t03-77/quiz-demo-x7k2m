# -*- coding: utf-8 -*-
"""肢どうしの語の重なりを上げるための選択肢書き直しパッチを適用する。

使い方: python tools/overlap_apply.py <パッチ.json> <EXAM-ID> [--dry]

any_apply_patch.py と違い、正解肢の text も書き換えられる。
4肢を「軸を共有した集合」に作り替えるとき、正解肢だけ形が違うと
「最短が正解」「最長が正解」という別の当てやすさが生まれるため。

そのぶん安全装置を厚くしてある:
  - id / exam / set / type / domain / level / n_correct / question /
    options[].letter / options[].correct が変わっていたら1件も書かずに中断
  - 選択肢の数が変わっていたら中断
  - 正解肢を書き換えた場合は、適用後に一覧で報告する

パッチ1件の形式:
  {"id": "...", "letter": "B", "text": "新しい選択肢テキスト", "expl": "差し替える解説全文"}
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"

IMMUTABLE = ("id", "exam", "set", "type", "domain", "level", "n_correct", "question")


def snap(q):
    return {k: q.get(k) for k in IMMUTABLE} | {
        "opts": [(o.get("letter"), bool(o.get("correct"))) for o in q.get("options") or []]
    }


def main(patch_path, exam):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, indents, index, before = {}, {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if q.get("exam") == exam:
                index[q["id"]] = (f, q)
                before[q["id"]] = snap(q)

    errors, touched, seen = [], set(), set()
    n_text = n_expl = 0
    changed_correct = []
    for p in patches:
        key = (p["id"], p["letter"])
        if key in seen:
            errors.append(f"{key}: 同じ選択肢へのパッチが重複")
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
        if "text" in p:
            if not p["text"].strip():
                errors.append(f"{p['id']}[{p['letter']}]: text が空")
                continue
            if p["text"] != o["text"]:
                if o.get("correct"):
                    changed_correct.append((p["id"], p["letter"], o["text"], p["text"]))
                o["text"] = p["text"]
                n_text += 1
                touched.add(f)
        if "expl" in p:
            new_ex = p["expl"]
            want = "正解です。" if o.get("correct") else "不正解です。"
            if not new_ex.lstrip().startswith(want):
                errors.append(f"{p['id']}[{p['letter']}]: 解説は「{want}」で始める必要がある")
                continue
            if new_ex != (o.get("explanation") or ""):
                o["explanation"] = new_ex
                n_expl += 1
                touched.add(f)

    # 不変項目が動いていないか
    for qid in sorted({p["id"] for p in patches}):
        if qid in index and snap(index[qid][1]) != before[qid]:
            errors.append(f"{qid}: 不変項目が変化した")

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        wmean = sum(len(o["text"]) for o in wrong) / len(wrong)
        flag = []
        if max(len(o["text"]) for o in wrong) <= max(len(o["text"]) for o in cor):
            flag.append("正解が最長")
        if min(len(o["text"]) for o in wrong) >= min(len(o["text"]) for o in cor):
            flag.append("正解が最短")
        print(f"  {qid} 正解{cmean:.0f} 誤答{wmean:.0f} "
              f"[{' '.join(str(len(o['text'])) for o in q['options'])}] {' '.join(flag)}")

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
    else:
        for f in touched:
            Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                               encoding="utf-8")
        print(f"OK: 選択肢 {n_text}件 / 解説 {n_expl}件 を更新 ({len(touched)}ファイル)")
    if changed_correct:
        print(f"-- 正解肢を変更した問題 {len(changed_correct)}件 --")
        for qid, letter, old, new in changed_correct:
            print(f"  {qid}[{letter}]\n    旧: {old}\n    新: {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
