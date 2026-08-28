# -*- coding: utf-8 -*-
"""公式模試と自作問題を、決め打ちしない多数の切り口で比べて差を洗い出す

これまでの検査は「指摘を受けてから作った観点」ばかりだった。
そのため、指摘されるまで気づけない欠陥が残り続けた。

このスクリプトは**観点を先に決めずに**、機械的に取れる特徴を総当たりで比較する。
差が大きいものが「まだ直していない箇所」として自動的に浮かび上がる。

比べる特徴（すべて公式との差で評価する）:
  A. 長さ・量        文字数、文の数、語数
  B. 構造            選択肢の数、正解の数、位置
  C. 語彙            どんな語をどれだけ使うか（動詞・接続・修飾）
  D. 関係            選択肢どうし、問題文と選択肢の重なり
  E. 記号・書式      数字、英数字、括弧、箇条書き
  F. 文型            文末表現、疑問の形

新しい観点を足したくなったら、下の FEATURES にひとつ関数を書き足すだけでよい。

使い方: python tools/audit_gap.py [--top N]
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


def load():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig" and q.get("options")]


def sents(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]


def opts(q):
    return [o.get("text", "") for o in q.get("options", [])]


def cor(q):
    return [o.get("text", "") for o in q.get("options", []) if o.get("correct")]


def wrong(q):
    return [o.get("text", "") for o in q.get("options", []) if not o.get("correct")]


WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def jac(a, b):
    A, B = set(WORD.findall(a)), set(WORD.findall(b))
    return len(A & B) / len(A | B) if A | B else 0


# ---- 比べる特徴。1問につき1つの数を返す関数を並べる ----------------
# 「割合」で見たいものは 0/1 を返す（平均すると割合になる）

FEATURES = [
    # A. 長さ・量
    ("問題文の文字数", lambda q: len(q.get("question", ""))),
    ("問題文の文の数", lambda q: len(sents(q.get("question", "")))),
    ("選択肢1つの文字数", lambda q: statistics.mean([len(t) for t in opts(q)]) if opts(q) else 0),
    ("選択肢の文字数のばらつき", lambda q: (max(len(t) for t in opts(q)) - min(len(t) for t in opts(q))) if len(opts(q)) > 1 else 0),
    ("解説1つの文字数", lambda q: statistics.mean([len(o.get("explanation") or "") for o in q["options"]]) if q.get("options") else 0),

    # B. 構造
    ("選択肢の数", lambda q: len(q.get("options", []))),
    ("正解の数", lambda q: q.get("n_correct") or sum(1 for o in q["options"] if o.get("correct"))),
    ("正解が最長か", lambda q: 1 if opts(q) and cor(q) and max(len(t) for t in opts(q)) == max(len(t) for t in cor(q)) else 0),
    ("正解が最短か", lambda q: 1 if opts(q) and cor(q) and min(len(t) for t in opts(q)) == min(len(t) for t in cor(q)) else 0),

    # C. 語彙
    ("選択肢が動詞で終わる", lambda q: statistics.mean([1 if re.search(r"(する|します|させる|行う)。?$", t) else 0 for t in opts(q)]) if opts(q) else 0),
    ("問題文に「最も」がある", lambda q: 1 if "最も" in q.get("question", "") else 0),
    ("問題文に否定条件がある", lambda q: 1 if re.search(r"(できない|してはならない|禁止|せずに|なしで|変更せず)", q.get("question", "")) else 0),
    ("選択肢に理由句がある", lambda q: statistics.mean([1 if re.search(r"(のため|により|によって|ので)", t) else 0 for t in opts(q)]) if opts(q) else 0),
    ("選択肢に条件句がある", lambda q: statistics.mean([1 if re.search(r"(場合|とき|ならば|であれば)", t) else 0 for t in opts(q)]) if opts(q) else 0),
    ("問題文に人物が登場する", lambda q: 1 if re.search(r"(企業|会社|組織|チーム|開発者|エンジニア|アーキテクト|担当者|部門)", q.get("question", "")) else 0),

    # D. 関係
    ("選択肢どうしの語の重なり", lambda q: statistics.mean([jac(a, b) for i, a in enumerate(opts(q)) for b in opts(q)[i+1:]]) if len(opts(q)) > 1 else 0),
    ("正解と最も似た誤答の一致度", lambda q: max([jac(c, w) for c in cor(q) for w in wrong(q)], default=0)),
    ("問題文と正解肢の重なり", lambda q: statistics.mean([jac(q.get("question", ""), c) for c in cor(q)]) if cor(q) else 0),
    ("問題文と誤答肢の重なり", lambda q: statistics.mean([jac(q.get("question", ""), w) for w in wrong(q)]) if wrong(q) else 0),

    # E. 記号・書式
    ("問題文の数字の個数", lambda q: len(re.findall(r"[0-9]+", q.get("question", "")))),
    ("問題文の英数字トークン数", lambda q: len(re.findall(r"[A-Za-z][A-Za-z0-9]+", q.get("question", "")))),
    ("選択肢の英数字トークン数", lambda q: statistics.mean([len(re.findall(r"[A-Za-z][A-Za-z0-9]+", t)) for t in opts(q)]) if opts(q) else 0),
    ("問題文に括弧がある", lambda q: 1 if re.search(r"[（(]", q.get("question", "")) else 0),
    ("選択肢が2文以上", lambda q: statistics.mean([1 if len(sents(t)) >= 2 else 0 for t in opts(q)]) if opts(q) else 0),

    # F. 文型
    ("問題文が疑問で終わる", lambda q: 1 if re.search(r"(か。|ですか。|でしょうか。|どれですか|どれか)\s*$", (q.get("question") or "").strip()) else 0),
    ("解説に転換表現がある", lambda q: statistics.mean([1 if re.search(r"(ただし|しかし|一方|ものの)", o.get("explanation") or "") else 0 for o in q["options"] if not o.get("correct")]) if wrong(q) else 0),
    ("解説が正解の優位に触れる", lambda q: statistics.mean([1 if re.search(r"(より|に比べ|最も|優れ)", o.get("explanation") or "") else 0 for o in q["options"] if o.get("correct")]) if cor(q) else 0),
]


def main():
    top = 12
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    off, mine = load()

    rows = []
    for name, fn in FEATURES:
        try:
            a = [fn(q) for q in off]
            b = [fn(q) for q in mine]
        except Exception as e:
            print("  (%s の計算に失敗: %s)" % (name, e))
            continue
        ma, mb = statistics.mean(a), statistics.mean(b)
        sd = statistics.pstdev(a) or 1
        # 公式の散らばりを1として、平均がどれだけ離れているか
        z = (mb - ma) / sd
        rows.append((abs(z), z, name, ma, mb))

    rows.sort(reverse=True)
    print("=" * 78)
    print(" 公式模試との差が大きい特徴（観点を決め打ちせず総当たりで比較）")
    print(" 公式 %d問 / 自作 %d問" % (len(off), len(mine)))
    print("=" * 78)
    print()
    print("%-26s %10s %10s %8s" % ("特徴", "公式", "自作", "隔たり"))
    print("-" * 78)
    for _, z, name, ma, mb in rows[:top]:
        mark = "  ★" if abs(z) >= 0.5 else ("  ・" if abs(z) >= 0.3 else "")
        print("%-26s %10.3f %10.3f %+8.2f%s" % (name, ma, mb, z, mark))

    print()
    print("  隔たり … 公式の散らばりを1としたときの平均の差")
    print("           ±0.5以上(★)は明確な差、±0.3以上(・)は要注意")
    print()
    big = [r for r in rows if r[0] >= 0.5]
    if big:
        print("次に検討すべき箇所:")
        for _, z, name, ma, mb in big:
            print("   %s … 公式 %.3f に対し 自作 %.3f（%s）"
                  % (name, ma, mb, "自作が多い" if z > 0 else "自作が少ない"))
    else:
        print("  ±0.5以上の差はありません")
    print()
    print("  ※ 新しい観点を試したいときは、このファイルの FEATURES に関数を1つ足すだけでよい")
    return 1 if big else 0


if __name__ == "__main__":
    sys.exit(main())
