# -*- coding: utf-8 -*-
"""選択肢を「軸を共有した集合」に作り替えるパッチを適用する。

対象は MLA-C01 / DVA-C02 / SOA-C03 のみ。他資格のIDが混ざっていたら1件も書かない。

この作業では 2x2 マトリクスを作るために正解肢の text も整える必要が出る。
そのため正解肢への書き込みを許すが、**問題ごとに correct_change: true を
明示したときだけ**許可する（うっかり正解肢を潰す事故を防ぐため）。
正誤フラグ (options[].correct) と letter / question などは一切触らない。

パッチ1件の形式:
  {"id": "MLA-C01_orig_026",
   "note": "型a: 評価指標の軸をそろえた",
   "correct_change": true,             # 正解肢の text を変えるときだけ必要
   "options": {"A": {"text": "...", "expl": "正解です。..."},
               "B": {"text": "...", "expl": "不正解です。..."}}}

使い方: python tools/axis_apply.py 資料/生成/_axis_mla_01.json [--dry]
"""
import json
import glob
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAMS = ("MLA-C01", "DVA-C02", "SOA-C03")
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')


def overlap(texts):
    s = [set(WORD.findall(t)) for t in texts if t]
    s = [x for x in s if x]
    if len(s) < 2:
        return 0.0
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else 0.0


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
            if q.get("exam") in EXAMS:
                index[q["id"]] = (f, q)

    errors = []
    touched = set()
    n_text = n_expl = 0
    seen = set()
    for p in patches:
        qid = p["id"]
        if qid in seen:
            errors.append(f"{qid}: パッチが重複")
            continue
        seen.add(qid)
        if qid not in index:
            errors.append(f"{qid}: 担当3資格に該当問題なし")
            continue
        f, q = index[qid]
        for letter, body in p["options"].items():
            os_ = [o for o in q["options"] if o["letter"] == letter]
            if not os_:
                errors.append(f"{qid}[{letter}]: 選択肢なし")
                continue
            o = os_[0]
            if o["correct"] and not p.get("correct_change"):
                errors.append(f"{qid}[{letter}]: 正解肢だが correct_change 指定なし")
                continue
            if "text" in body:
                t = body["text"].strip()
                if not t:
                    errors.append(f"{qid}[{letter}]: text が空")
                    continue
                if len(t) > 150:
                    errors.append(f"{qid}[{letter}]: text が150字超 ({len(t)})")
                    continue
                if t != o["text"]:
                    o["text"] = t
                    n_text += 1
                    touched.add(f)
            if "expl" in body:
                ex = body["expl"].strip()
                head = "正解です" if o["correct"] else "不正解です"
                if not ex.startswith(head):
                    errors.append(f"{qid}[{letter}]: 解説は「{head}。」で始める必要がある")
                    continue
                if ex != o.get("explanation"):
                    o["explanation"] = ex
                    n_expl += 1
                    touched.add(f)

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    for qid in [p["id"] for p in patches]:
        q = index[qid][1]
        texts = [o["text"] for o in q["options"]]
        cor = [len(o["text"]) for o in q["options"] if o["correct"]]
        wrong = [len(o["text"]) for o in q["options"] if not o["correct"]]
        flag = "正解が最長" if max(wrong) <= max(cor) else ""
        multi = sum(1 for t in texts if t.count("。") >= 2)
        print(f"  {qid} overlap={overlap(texts):.3f} 文長{texts and [len(t) for t in texts]} "
              f"2文以上{multi}/{len(texts)} {flag}")

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0
    for f in touched:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                           encoding="utf-8")
    print(f"OK: text {n_text}件 / 解説 {n_expl}件 を更新 ({len(touched)}ファイル)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
