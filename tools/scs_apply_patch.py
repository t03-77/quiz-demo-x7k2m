# -*- coding: utf-8 -*-
"""SCS-C03 の作り直しパッチを適用する。

狙いは「消去法で解けてしまう」状態の解消。
  - 捨て札の誤答肢を、実在する構成の一見もっともらしい案に差し替える
  - 問題文の要件が選択肢を1つずつ潰す作りをやめ、複数肢が最後まで残るようにする
  - 問題文の語がそのまま正解名になるキーワード直結を言い換える

正解肢の text と、id/exam/set/type/domain/level/n_correct/letter/correct は
触らない。パッチが対象外を書き換えようとしたら、1件も書き込まずに中断する
(過去に別内容で上書きして問題が消えかけた事故があるため)。

パッチ1件の形式:
  # 誤答肢の差し替え
  {"id": "...", "letter": "B",
   "text": "新しい誤答肢テキスト",
   "expl": "差し替える解説全文"}          # 誤答の解説は「不正解です。」で始める
  # 正解肢の解説だけ直す(text は触らない)
  {"id": "...", "letter": "A", "expl": "..."}
  # 問題文の言い換え
  {"id": "...", "question": "新しい問題文"}

使い方: python tools/scs_apply_patch.py 資料/生成/_scs_patch_01.json [--dry]
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAM = "SCS-C03"


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files = {}
    indents = {}
    index = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if q.get("exam") == EXAM:
                index[q["id"]] = (f, q)

    errors = []
    touched_files = set()
    n_text = n_expl = n_q = 0
    seen = set()
    for p in patches:
        qid = p["id"]
        if qid not in index:
            errors.append(f"{qid}: 該当問題なし")
            continue
        f, q = index[qid]

        # 問題文の差し替え
        if "question" in p:
            key = (qid, "__question__")
            if key in seen:
                errors.append(f"{qid}: 問題文パッチが重複")
                continue
            seen.add(key)
            newq = p["question"]
            if not newq.strip():
                errors.append(f"{qid}: question が空")
                continue
            if not (150 <= len(newq) <= 420):
                errors.append(f"{qid}: question の長さ {len(newq)}字 (150〜420字に収める)")
                continue
            if newq != q["question"]:
                q["question"] = newq
                n_q += 1
                touched_files.add(f)
            if "letter" not in p:
                continue

        if "letter" not in p:
            continue
        key = (qid, p["letter"])
        if key in seen:
            errors.append(f"{key}: 同じ選択肢へのパッチが重複")
            continue
        seen.add(key)
        opts = [o for o in q["options"] if o["letter"] == p["letter"]]
        if not opts:
            errors.append(f"{qid}[{p['letter']}]: 該当選択肢なし")
            continue
        o = opts[0]
        if "text" in p:
            if o["correct"]:
                errors.append(f"{qid}[{p['letter']}]: 正解肢の text は書き換え禁止")
                continue
            if not p["text"].strip():
                errors.append(f"{qid}[{p['letter']}]: text が空")
                continue
            if p["text"] != o["text"]:
                o["text"] = p["text"]
                n_text += 1
                touched_files.add(f)
        if "expl" in p:
            new_ex = p["expl"]
            if not new_ex.strip():
                errors.append(f"{qid}[{p['letter']}]: expl が空")
                continue
            head = "正解です" if o["correct"] else "不正解です"
            if not new_ex.lstrip().startswith(head):
                errors.append(f"{qid}[{p['letter']}]: 解説は「{head}。」で始める必要がある")
                continue
            if new_ex != o.get("explanation"):
                o["explanation"] = new_ex
                n_expl += 1
                touched_files.add(f)

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        if not cor or not wrong:
            continue
        cmax = max(len(o["text"]) for o in cor)
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        wmean = sum(len(o["text"]) for o in wrong) / len(wrong)
        ng = [f"{o['letter']}:{len(o['text'])}" for o in wrong
              if not (0.8 * cmean <= len(o["text"]) <= 1.2 * cmean)]
        flag = []
        if max(len(o["text"]) for o in wrong) <= cmax:
            flag.append("正解が最長")
        if ng:
            flag.append("範囲外 " + ",".join(ng))
        print(f"  {qid} Q{len(q['question'])}字 正解{cmean:.0f} 誤答平均{wmean:.0f} 比{cmean/wmean:.2f} "
              f"[{' '.join(str(len(o['text'])) for o in q['options'])}] {' / '.join(flag)}")

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0

    for f in touched_files:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                           encoding="utf-8")
    print(f"OK: 問題文 {n_q}件 / 誤答肢テキスト {n_text}件 / 解説 {n_expl}件 を更新 "
          f"({len(touched_files)}ファイル)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
