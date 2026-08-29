# -*- coding: utf-8 -*-
"""2正解5肢の問題を、正解肢を1つ取り除いて 1正解4肢 にする。

## なぜ必要か

公式模試の複数選択の比率と、自作問題の比率がずれていた。
MLA-C01 は公式が「1つ選択 93% / 2つ選択 6%」なのに対し、自作は 78% / 22% で
2つ選択が3倍以上あった。本番と出題の形が違うと、演習の感覚がずれる。

## 使ってよい問題・いけない問題

**取り除いてよいのは「2つの正解が代替関係にある」問題だけ。**
片方だけでも問題文の要件を満たすもの。

  例) MLA-C01_orig_029「トレーニングが発散している」
      A 学習率を下げる / B 勾配クリッピングを適用する
      → どちらも単独で有効な対処。B を取り除いても問題は成立する

**2つの正解が組み合わせで1つの要件を満たす問題には使わないこと。**

  例) MLA-C01_orig_020「PII を含むデータを使えない」
      A 機密データ検出で PII を識別する / B 検出した PII を秘匿化する
      → A だけでは検出しただけで秘匿化していない。片方を消すと問題が成立しない

判断は人が行う。このツールは判断しない。

## 安全装置

- 対象が2正解でなければ中断する
- 取り除く肢が正解でなければ中断する
- 問題文に「組み合わせ」が含まれていたら中断する(1つ選択の問題文として不自然になるため)
- 解説に選択肢記号への参照があれば警告する(振り直しでずれるため)

使い方: python tools/make_single_answer.py 資料/生成/_single_xxx.json [--dry]

パッチ形式:
  [{"id": "...", "drop": "B"},
   {"id": "...", "drop": "B",
    "q_sub": ["どの組み合わせの手順を実行すべきですか", "どうすべきですか"]}]

問題文が「どの組み合わせの手順を〜」のときは、1つ選択にすると文が合わなくなる。
`q_sub` で置換を指定すること。指定がなければ中断する。
"""
import glob
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
REF = re.compile(r"(選択肢\s*[A-F]|肢\s*[A-F]|[（(][A-F][）)])")
LETTERS = "ABCDEF"


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
            index.setdefault(q["id"], (f, q))

    errors, warns, touched, done = [], [], set(), []
    for p in patches:
        qid, drop = p["id"], p["drop"]
        if qid not in index:
            errors.append("%s: 該当問題なし" % qid)
            continue
        f, q = index[qid]
        opts = q.get("options") or []
        cor = [o for o in opts if o.get("correct")]
        if len(cor) != 2:
            errors.append("%s: 正解が%d個(2個の問題にだけ使える)" % (qid, len(cor)))
            continue
        tgt = [o for o in opts if o["letter"] == drop]
        if not tgt:
            errors.append("%s[%s]: 該当選択肢なし" % (qid, drop))
            continue
        if not tgt[0].get("correct"):
            errors.append("%s[%s]: 誤答肢は取り除けない(この作業は正解を1つ減らすもの)" % (qid, drop))
            continue
        new_q = None
        if "q_sub" in p:
            old, new = p["q_sub"]
            if q.get("question", "").count(old) != 1:
                errors.append("%s: q_sub の置換対象が%d箇所" % (qid, q.get("question", "").count(old)))
                continue
            new_q = q["question"].replace(old, new)
            if "組み合わせ" in new_q:
                errors.append("%s: 置換後も問題文に「組み合わせ」が残っている" % qid)
                continue
        elif "組み合わせ" in q.get("question", ""):
            errors.append("%s: 問題文に「組み合わせ」がある。q_sub で言い換えを指定すること" % qid)
            continue
        for o in opts:
            if REF.search(o.get("explanation") or ""):
                warns.append("%s[%s]: 解説が選択肢記号を参照している" % (qid, o["letter"]))

        rest = [o for o in opts if o["letter"] != drop]
        for i, o in enumerate(rest):
            o["letter"] = LETTERS[i]
        q["options"] = rest
        q["n_correct"] = 1
        if new_q is not None:
            q["question"] = new_q
        touched.add(f)
        done.append((qid, drop, len(rest)))

    if errors:
        print("NG: %d件のため何も書き込みませんでした" % len(errors))
        for e in errors:
            print("  " + e)
        return 1
    for w in warns:
        print("  警告 " + w)
    for qid, drop, n in done:
        print("  %s  %s を取り除いて 1正解%d肢 にした" % (qid, drop, n))

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0
    for f in touched:
        Path(f).write_text(
            json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1), encoding="utf-8")
    print("OK: %d問を 1正解4肢 に変更 (%dファイル)" % (len(done), len(touched)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
