# -*- coding: utf-8 -*-
"""公式問題の「書き方の癖」を統計で洗い出し、自作と比べる

これまで測ってきたのは、指摘を受けて気づいた個別の欠陥だった。
このスクリプトは、指摘を待たずに**文章の作りそのもの**を機械的に比較する。

測るもの:
  1. 問題文の組み立て … 文の数、段落の数、数値の個数
  2. 選択肢の文法      … 何で終わるか、何で始まるか、文がいくつあるか
  3. 選択肢どうしの関係 … 4肢の語彙がどれだけ重なっているか（軸を共有しているか）
  4. 評価軸の置き場所   … 「最も〜」が問題文のどこに出るか
  5. 解説の組み立て     … 文の数、接続表現の使い方

差が大きい項目が、そのまま次に直すべき箇所になる。

使い方: python tools/audit_pattern.py
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


def sentences(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]


def pct(part, whole):
    return 100 * part // max(1, whole)


# ---- 1. 問題文の組み立て ----------------------------------------

def stem_stats(qs):
    sn = [len(sentences(q.get("question", ""))) for q in qs]
    num = [len(re.findall(r"[0-9]+\s*(?:分|時間|日|か月|年|TB|GB|MB|ミリ秒|%|件|台|回|アカウント|インスタンス)",
                          q.get("question", ""))) for q in qs]
    return {
        "文の数": statistics.median(sn),
        "数値の個数": statistics.median(num),
        "数値なし": pct(sum(1 for x in num if x == 0), len(qs)),
    }


# ---- 2. 選択肢の文法 --------------------------------------------

VERB_END = re.compile(r"(する|します|させる|行う|使う|使用する|設定する|作成する|有効[には]する|適用する)。?$")
NOUN_END = re.compile(r"[ぁ-んァ-ヶ一-龥A-Za-z0-9)）]$")


def option_stats(qs):
    ends, starts, nsent = Counter(), Counter(), []
    for q in qs:
        for o in q["options"]:
            t = (o.get("text") or "").strip()
            if not t:
                continue
            ends["動詞で終わる" if VERB_END.search(t) else "体言などで終わる"] += 1
            m = re.match(r"^(?:Amazon|AWS)?\s*([A-Za-z][A-Za-z0-9]*|[ぁ-んァ-ヶ一-龥]{2,6})", t)
            if m:
                starts[m.group(1)] += 1
            nsent.append(len(sentences(t)))
    top = starts.most_common(1)
    return {
        "動詞で終わる": pct(ends["動詞で終わる"], sum(ends.values())),
        "1肢あたりの文数": statistics.median(nsent) if nsent else 0,
        "2文以上": pct(sum(1 for x in nsent if x >= 2), len(nsent)) if nsent else 0,
        "先頭語の最頻": ("%s(%d%%)" % (top[0][0], pct(top[0][1], sum(starts.values())))) if top else "-",
    }


# ---- 3. 選択肢どうしの関係 --------------------------------------

WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def overlap_stats(qs):
    """4肢が同じ語をどれだけ共有しているか。
    公式の4肢は「独立した別案」ではなく軸を共有した集合なので、重なりが大きいはず。"""
    vals = []
    for q in qs:
        sets = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
        sets = [s for s in sets if s]
        if len(sets) < 2:
            continue
        pairs = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                u = sets[i] | sets[j]
                if u:
                    pairs.append(len(sets[i] & sets[j]) / len(u))
        if pairs:
            vals.append(statistics.mean(pairs))
    return {
        "肢どうしの語の重なり": round(statistics.mean(vals), 3) if vals else 0,
        "重なりが薄い問題(<0.1)": pct(sum(1 for v in vals if v < 0.1), len(vals)) if vals else 0,
    }


# ---- 4. 評価軸の置き場所 ----------------------------------------

AXIS = re.compile(r"(最も|最小限|最大限|最少|できるだけ|なるべく)")


def axis_stats(qs):
    has = tail = 0
    for q in qs:
        s = sentences(q.get("question", ""))
        if not s:
            continue
        if any(AXIS.search(x) for x in s):
            has += 1
            if AXIS.search(s[-1]):
                tail += 1
    return {
        "評価軸あり": pct(has, len(qs)),
        "軸が最後の一文にある": pct(tail, has) if has else 0,
    }


# ---- 5. 解説の組み立て ------------------------------------------

TURN = re.compile(r"(ただし|しかし|ものの|一方|ため|ので|には向|は満たせ|できません|ありません)")


def expl_stats(qs):
    ns, turn, tot = [], 0, 0
    for q in qs:
        for o in q["options"]:
            if o.get("correct"):
                continue
            e = (o.get("explanation") or "").strip()
            if not e:
                continue
            tot += 1
            ns.append(len(sentences(e)))
            if TURN.search(e):
                turn += 1
    return {
        "誤答解説の文数": statistics.median(ns) if ns else 0,
        "転換表現あり": pct(turn, tot),
    }


def per_exam(off, mine, fn, key):
    """資格ごとに公式と自作を比べる。

    全資格をまとめた平均で比べてはいけない。
    実際、語の重なりは公式が SAP-C02 0.409 / DOP-C02 0.438 に対し
    CLF-C02 0.119 / AIF-C01 0.157 と3倍以上の開きがある。
    全体平均(0.267)を目標にすると、基礎資格には過剰な水増しを強いることになる
    （実際にそれで CLF-C02 に不要な作業を指示しかけた）。
    """
    rows = []
    for ex in sorted({q["exam"] for q in mine}):
        o = [q for q in off if q.get("exam") == ex]
        m = [q for q in mine if q["exam"] == ex]
        if not o or not m:
            continue
        ov, mv = fn(o).get(key, 0), fn(m).get(key, 0)
        rows.append((ex, ov, mv))
    return rows


def main():
    off, mine = load()
    groups = [
        ("1. 問題文の組み立て", stem_stats),
        ("2. 選択肢の文法", option_stats),
        ("3. 選択肢どうしの関係", overlap_stats),
        ("4. 評価軸の置き場所", axis_stats),
        ("5. 解説の組み立て", expl_stats),
    ]
    print("=" * 74)
    print(" 公式問題の書き方の癖と、自作との差")
    print(" 公式 %d問 / 自作 %d問" % (len(off), len(mine)))
    print("=" * 74)

    gaps = []
    for title, fn in groups:
        o, m = fn(off), fn(mine)
        print()
        print(title)
        for k in o:
            ov, mv = o[k], m[k]
            mark = ""
            # 割合の項目で 12pt 以上、比率の項目で 1.5倍以上離れていたら印をつける
            if isinstance(ov, int) and isinstance(mv, int) and abs(ov - mv) >= 12:
                mark = "   ★差が大きい"
                gaps.append((title, k, ov, mv))
            elif isinstance(ov, float) and ov and (mv / ov > 1.5 or mv / ov < 0.67):
                mark = "   ★差が大きい"
                gaps.append((title, k, ov, mv))
            print("   %-22s 公式 %-10s 自作 %-10s%s" % (k, ov, mv, mark))

    print()
    print("=" * 74)
    if gaps:
        print("次に直すべき箇所（★は全資格をまとめた値。資格ごとの内訳を必ず見ること）:")
        for t, k, ov, mv in gaps:
            print("   [%s] %s … 公式 %s に対し 自作 %s" % (t.split(". ")[1], k, ov, mv))

    # 全資格をまとめた平均は資格差に埋もれる。主要な項目は必ず資格ごとにも出す。
    # （公式の語の重なりは SAP 0.409 / CLF 0.119 と3倍以上違う）
    ng_exam = []
    for title, fn, key in [("2. 選択肢の文法", option_stats, "2文以上"),
                           ("3. 選択肢どうしの関係", overlap_stats, "肢どうしの語の重なり")]:
        print()
        print("  ▼ %s（資格ごと。全体平均では資格差が埋もれる）" % key)
        for ex, ov, mv in per_exam(off, mine, fn, key):
            ratio = (mv / ov) if ov else 1
            # 2026-09-03: 超過も検出するようにした。
            # 公式より高すぎるのも「不自然な手がかり」で、公式との乖離であることに変わりはない
            # （鉄則4「上下どちらにずれても手がかりになる」）。実際、語の重なりを上げる作業で
            # AIF-C01 と CLF-C02 が公式を大きく超えていたのに、不足しか見ていなかったため
            # 検出できていなかった。
            gap = abs(mv - ov)
            floor = 0.03 if "重なり" in key else 5      # 小さい値での比率の暴れを抑える
            mark = ""
            if ratio < 0.9 and gap >= floor:
                mark = "   ★不足 %.0f%%" % (100 * ratio)
                ng_exam.append(("不足", key, ex, ov, mv))
            elif ratio > 1.25 and gap >= floor:
                mark = "   ★超過 %.0f%%" % (100 * ratio)
                ng_exam.append(("超過", key, ex, ov, mv))
            print("     %-9s 公式 %-8s 自作 %-8s%s" % (ex, round(ov, 3), round(mv, 3), mark))

    print()
    if ng_exam:
        short = sum(1 for x in ng_exam if x[0] == "不足")
        over = len(ng_exam) - short
        print("資格ごとに見て公式から離れているもの: %d件（不足 %d / 超過 %d）" % (len(ng_exam), short, over))
        if over:
            print("  ※超過は「公式より高すぎる」状態。下げる方向の調整が要る（鉄則4）")
    elif not gaps:
        print("この観点では、公式と目立った差はありません")
    return 1 if (gaps or ng_exam) else 0


if __name__ == "__main__":
    sys.exit(main())
