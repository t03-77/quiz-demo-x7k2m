# -*- coding: utf-8 -*-
"""公式問題の全問から、その資格の「作問ガイド」を作る

これまで問題を作るとき渡していたのは各資格8問の実例だけだった(資料/校正サンプル/)。
1290問持っているのに88問しか使っておらず、これが
「試験範囲が狭い・内容が簡単」の直接の原因になっていた。

このスクリプトは公式問題を全問走査して、次を1ファイルにまとめる:

  1. 数値で示した基準 … 選択肢の形、問題文と選択肢の長さ、評価軸の使われ方
  2. 誤答の材料 …… 公式が誤答に使っているサービス・機能の一覧(頻度つき)
  3. 制約の書き方 … 公式が問題文で使っている制約表現の実例
  4. 代表例 ……… 形・長さ・評価軸が偏らないように選んだ実例

実例をただ並べるのではなく「守るべき数値」を先に示すのが要点。
「良い問題を作れ」では守られないが、「1正解なら4肢」なら守られる。

使い方: python tools/make_exam_guide.py [EXAM_ID]
出力  : 資料/作問ガイド/{EXAM}.md
"""
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
OUT_DIR = BASE / "資料" / "作問ガイド"

# 評価軸(この語が入ると「複数の正解候補から1つに絞る」問題になる)
AXIS = [("運用負荷", r"(運用(上の)?(負荷|オーバーヘッド)|オペレーション(上の)?(負荷|効率))"),
        ("コスト", r"(コスト効率|最も(低|安)コスト|費用対効果|最小のコスト)"),
        ("可用性", r"(可用性|耐障害性|回復力)"),
        ("性能", r"(レイテンシー|スループット|パフォーマンス)"),
        ("セキュリティ", r"(最小権限|セキュリティ(上|要件)|安全)"),
        ("実装の速さ", r"(最も(少ない|短い)(開発|実装|労力)|コード変更を最小)")]

# 問題文でよく使われる制約の型
CONSTRAINT = [("禁止・不可", r"[^。\n]*(できない|してはならない|禁止|認められ(ない|ておらず)|使用できません)[^。\n]*。"),
              ("既存の構成", r"[^。\n]*(既に|すでに|現在)[^。\n]*(使用|運用|構成|導入)[^。\n]*。"),
              ("定量の要件", r"[^。\n]*[0-9]+\s*(分|時間|日|か月|TB|GB|ミリ秒|%|件|台|アカウント)[^。\n]*。"),
              ("体制の制約", r"[^。\n]*(チーム|担当者|人員|要員|運用担当)[^。\n]*(ない|限られ|少ない|抱えて)[^。\n]*。")]


def load(exam):
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    qs = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in qs if q.get("exam") == exam and q.get("options")]


def shape(q):
    nc = q.get("n_correct") or sum(1 for o in q["options"] if o.get("correct"))
    return nc, len(q["options"])


def axis_of(q):
    t = q.get("question", "")
    return [name for name, rx in AXIS if re.search(rx, t)]


def pick_examples(qs, n=12):
    """形・長さ・評価軸が偏らないように実例を選ぶ

    先頭から8問取ると、たまたま似た型ばかりになる。
    「1正解4肢で運用負荷を問うもの」「2正解5肢」「3正解6肢」…と
    組み合わせごとに1問ずつ拾って、作り手が型の違いを見られるようにする。
    """
    buckets = {}
    for q in qs:
        key = (shape(q), tuple(sorted(axis_of(q))[:1]))
        buckets.setdefault(key, []).append(q)
    out = []
    for key in sorted(buckets, key=lambda k: -len(buckets[k])):
        group = sorted(buckets[key], key=lambda q: len(q.get("question", "")))
        out.append(group[len(group) // 2])      # その型の中央的な長さのものを選ぶ
        if len(out) >= n:
            break
    while len(out) < n and len(out) < len(qs):
        for q in qs:
            if q not in out:
                out.append(q)
                break
    return out


def fmt_q(q):
    nc, nopt = shape(q)
    s = ["### %s（%d正解 / %d肢, 問題文%d字）" % (q.get("id", "?"), nc, nopt, len(q.get("question", "")))]
    s.append("")
    s.append("**問題文**")
    s.append("")
    s.append(q.get("question", "").strip())
    s.append("")
    s.append("**選択肢**")
    s.append("")
    for o in q["options"]:
        mark = "正解" if o.get("correct") else "誤答"
        s.append("- **%s. [%s]** %s" % (o.get("letter"), mark, (o.get("text") or "").strip()))
        ex = (o.get("explanation") or "").strip()
        if ex:
            s.append("  - 解説（%d字）: %s" % (len(ex), ex))
    return "\n".join(s)


def build(exam):
    qs = load(exam)
    if not qs:
        return None
    exam_qs = [q for q in qs if q.get("set") in ("exam", "pretest")]
    base = exam_qs or qs

    L = sorted(len(q.get("question", "")) for q in base)
    OL = sorted(len(o.get("text", "")) for q in base for o in q["options"])
    shapes = Counter(shape(q) for q in base)
    axes = Counter(a for q in base for a in axis_of(q))
    noaxis = sum(1 for q in base if not axis_of(q))

    # 誤答に使われているサービス・機能
    SVC = re.compile(r"(?:Amazon|AWS)\s+([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2})")
    wrong = Counter()
    for q in base:
        for o in q["options"]:
            if not o.get("correct"):
                for m in SVC.finditer(o.get("text", "")):
                    wrong[m.group(1).strip()] += 1

    # 制約表現の実例
    cons = {}
    for name, rx in CONSTRAINT:
        hits = []
        for q in base:
            for m in re.finditer(rx, q.get("question", "")):
                t = m.group(0).strip()
                if 15 < len(t) < 90:
                    hits.append(t)
        cons[name] = hits[:6]

    o = []
    o.append("# %s 作問ガイド（公式%d問から作成）" % (exam, len(qs)))
    o.append("")
    o.append("公式問題を**全問**走査して作った基準。実例だけでなく、守るべき数値を先に示す。")
    o.append("以前は各資格8問の実例しか渡しておらず、それが「試験範囲が狭い・内容が簡単」の原因だった。")
    o.append("")
    o.append("## 1. 守るべき数値")
    o.append("")
    o.append("| 項目 | 公式の実測 |")
    o.append("|---|---|")
    o.append("| 出題の形 | %s |" % " / ".join(
        "**%d正解%d肢** %d問(%d%%)" % (k[0], k[1], v, 100 * v // len(base))
        for k, v in shapes.most_common()))
    o.append("| 問題文の長さ | 中央 **%d字**（下位10%% %d字 / 上位10%% %d字）|" % (
        statistics.median(L), L[int(len(L) * .1)], L[int(len(L) * .9)]))
    o.append("| 選択肢1つの長さ | 中央 **%d字**（下位10%% %d字 / 上位10%% %d字）|" % (
        statistics.median(OL), OL[int(len(OL) * .1)], OL[int(len(OL) * .9)]))
    o.append("| 評価軸あり | %d%%（軸なしで要件だけで決まる問題が %d%%）|" % (
        100 * (len(base) - noaxis) // len(base), 100 * noaxis // len(base)))
    o.append("")
    o.append("**この形以外は作らないこと。** 例えば「1正解5肢」は公式に%d問しかない。" %
             shapes.get((1, 5), 0))
    o.append("")
    o.append("## 2. 評価軸の使われ方")
    o.append("")
    for name, c in axes.most_common():
        o.append("- **%s** … %d問（%d%%）" % (name, c, 100 * c // len(base)))
    o.append("")
    o.append("軸は「4肢とも要件は満たすが、この軸で1つが勝つ」という形で使う。")
    o.append("軸を消しても正解が変わらないなら、その軸は効いていない。")
    o.append("")
    o.append("## 3. 誤答に使われているサービス・機能（頻度順）")
    o.append("")
    o.append("公式は誤答にも**実在するサービスの、もっともらしい使い方**を置く。")
    o.append("「人手でやる」「手作業で集約する」「何もしない」といった誤答は公式には存在しない。")
    o.append("")
    o.append(" / ".join("%s(%d)" % (s, c) for s, c in wrong.most_common(40)))
    o.append("")
    o.append("## 4. 問題文で使われている制約の実例")
    o.append("")
    o.append("制約は1つが誤答1つを落とすように書く。どの誤答も落とさない制約は飾りでしかない。")
    o.append("")
    for name, hits in cons.items():
        if not hits:
            continue
        o.append("**%s**" % name)
        o.append("")
        for h in hits:
            o.append("- %s" % h)
        o.append("")
    o.append("## 5. 実例（形・長さ・評価軸が偏らないように選出）")
    o.append("")
    for q in pick_examples(base):
        o.append(fmt_q(q))
        o.append("")
    return "\n".join(o)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    qs = d.get("questions", d) if isinstance(d, dict) else d
    exams = [sys.argv[1]] if len(sys.argv) > 1 else sorted({q["exam"] for q in qs if q.get("options")})
    for ex in exams:
        text = build(ex)
        if not text:
            print("skip: %s (公式問題なし)" % ex)
            continue
        p = OUT_DIR / ("%s.md" % ex)
        p.write_text(text, encoding="utf-8")
        print("%s → %s (%d字)" % (ex, p.name, len(text)))


if __name__ == "__main__":
    main()
