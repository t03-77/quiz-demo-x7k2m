# -*- coding: utf-8 -*-
"""問題が「簡単すぎないか」を公式模試と比べて測る

字数だけを見ていると、短くはないが実は考えなくても解ける問題を見逃す。
本番より簡単な問題ばかり解いても合格の役に立たないため、
受験者が「中身を知らなくても当てられてしまう」手がかりを機械的に数える。

測る手がかり:
  1. 正解肢が最長      … 「一番長い選択肢が正解」という当て方が通用するか
  2. キーワードリーク  … 問題文の特徴語が正解肢だけに出てきて、照合だけで解けるか
  3. 誤答の絶対語      … 「すべて」「常に」「決して」など、読んだ瞬間に切れる誤答
  4. 誤答の使い回し    … 同じ誤答文が問題をまたいで何度も出てくる
  5. 選択肢の長さの差  … 正解だけ明らかに長い/短いと目立つ

いずれも公式模試を基準にする。公式より手がかりが多ければ「本番より簡単」。
"""
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"

# 読んだ瞬間に誤答と分かってしまう言い切り表現
ABSOLUTE = re.compile(r"(すべての場合|常に|必ず|決して|一切|例外なく|唯一の方法|不可能です|できません)")
# 特徴語として扱うもの: サービス名や機能名になりうる英数字の連なり
TERM = re.compile(r"[A-Z][A-Za-z0-9]{2,}(?:\s+[A-Z][A-Za-z0-9]+)*")
# どの問題にも出る一般語は特徴語から除く
COMMON = {"AWS", "Amazon", "IAM", "VPC", "API", "The", "This", "AZ", "EC2", "S3"}


def load_official():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    qs = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in qs if q.get("set") in ("exam", "pretest")]


def load_mine():
    js = open(ORIG, encoding="utf-8").read()
    qs = json.loads(js[js.index("["): js.rindex("]") + 1])
    return [q for q in qs if q.get("set") == "orig"]


def terms(text):
    return {m.group(0) for m in TERM.finditer(text or "")} - COMMON


def measure(qs, label):
    """選択式の問題だけを対象に手がかりを数える"""
    qs = [q for q in qs if (q.get("type", "choice") == "choice") and q.get("options")]
    longest = leak = longest_wrong = 0
    abs_q = 0
    ratios = []
    dup = Counter()
    n = 0
    for q in qs:
        opts = q["options"]
        cor = [o for o in opts if o.get("correct")]
        wrong = [o for o in opts if not o.get("correct")]
        if not cor or not wrong:
            continue
        n += 1
        lens = [len(o.get("text", "")) for o in opts]
        clen = statistics.mean(len(o.get("text", "")) for o in cor)
        wlen = statistics.mean(len(o.get("text", "")) for o in wrong)

        # 1. 正解が最長か(複数正解なら、正解のどれかが最長なら該当)
        if max(lens) == max(len(o.get("text", "")) for o in cor):
            longest += 1
        else:
            # 誤答を長くしすぎると「最長は必ず誤答」という逆の当て方が生まれる。
            # 正解が最長になる割合を下げるだけでは足りず、こちらも公式と比べる必要がある。
            longest_wrong += 1

        # 2. 問題文の特徴語が正解にだけ出てくるか
        qt = terms(q.get("question", ""))
        if qt:
            in_cor = qt & set().union(*[terms(o.get("text", "")) for o in cor])
            in_wrong = set().union(*[terms(o.get("text", "")) for o in wrong]) if wrong else set()
            if in_cor and not (in_cor & in_wrong):
                leak += 1

        # 3. 誤答に言い切り表現があるか
        if any(ABSOLUTE.search(o.get("text", "")) for o in wrong):
            abs_q += 1

        # 4. 誤答文の使い回し
        for o in wrong:
            t = (o.get("text") or "").strip()
            if len(t) > 10:
                dup[t] += 1

        # 5. 正解と誤答の長さの比
        if wlen:
            ratios.append(clen / wlen)

    reused = sum(1 for t, c in dup.items() if c >= 3)
    return {
        "label": label,
        "n": n,
        "longest": 100 * longest // n if n else 0,
        "longest_wrong": 100 * longest_wrong // n if n else 0,
        "leak": 100 * leak // n if n else 0,
        "abs": 100 * abs_q // n if n else 0,
        "ratio": statistics.median(ratios) if ratios else 0,
        "reused": reused,
    }


def main():
    off = load_official()
    mine = load_mine()
    exams = sorted({q["exam"] for q in mine})

    print("手がかりが多いほど「考えなくても当てられる」= 本番より簡単ということ")
    print()
    print("%-9s %-6s %10s %12s %10s %10s" % ("資格", "対象", "正解が最長", "キーワード一致", "誤答に断定", "正解/誤答の長さ比"))
    print("-" * 76)

    flags = []
    for ex in exams:
        o = [q for q in off if q.get("exam") == ex]
        m = [q for q in mine if q["exam"] == ex]
        if not o:
            continue
        ro = measure(o, "公式")
        rm = measure(m, "自作")
        for r in (ro, rm):
            print("%-9s %-6s %8d%%   %10d%%   %8d%%   %12.2f" % (
                ex if r is ro else "", r["label"], r["longest"], r["leak"], r["abs"], r["ratio"]))
        # 公式より手がかりが目立って多い項目を控える
        if rm["longest"] - ro["longest"] >= 15:
            flags.append((ex, "正解が最長になりやすい", ro["longest"], rm["longest"]))
        if rm["longest_wrong"] - ro["longest_wrong"] >= 15:
            flags.append((ex, "最長は誤答という癖がある", ro["longest_wrong"], rm["longest_wrong"]))
        if rm["leak"] - ro["leak"] >= 15:
            flags.append((ex, "問題文の語が正解にだけ出る", ro["leak"], rm["leak"]))
        if rm["abs"] - ro["abs"] >= 15:
            flags.append((ex, "誤答が断定表現で切れる", ro["abs"], rm["abs"]))
        if rm["reused"] > ro["reused"] * 2 + 3:
            flags.append((ex, "同じ誤答文の使い回し", ro["reused"], rm["reused"]))
        print()

    print("=" * 76)
    if flags:
        print("本番より簡単になっている可能性がある箇所:")
        for ex, why, a, b in flags:
            print("  %-9s %-26s 公式 %s → 自作 %s" % (ex, why, a, b))
        return 1
    print("公式模試と比べて、当てやすさが目立って高い資格はありません")
    return 0


if __name__ == "__main__":
    sys.exit(main())
