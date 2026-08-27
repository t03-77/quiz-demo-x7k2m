# -*- coding: utf-8 -*-
"""チェックリスト37項目の充足状況を出す

`資料/生成/_review_criteria.md` は公式問題61問を精読して導いた「良い問題」の条件。
一方 `audit_all.py` が測っていたのはそのうち5項目だけだった。
観点そのものに抜けがあることに気づけないのが、後追いの修正を繰り返した原因。

このスクリプトは全37項目を並べ、それぞれを次の3つに分類して表示する:

  [測定] … 機械で判定できて、実装済み
  [要AI] … 機械では判定できず、AIまたは人が読む必要がある
  [未実装] … 機械化できるはずだが、まだ実装していない

**[要AI] と [未実装] を必ず表示する。** 出さないと
「検査が全部通った＝問題なし」と誤解する。

使い方: python tools/audit_criteria.py
"""
import json
import re
import statistics
import sys
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


# ---- 個別の測定 -------------------------------------------------

CONSTRAINT = re.compile(
    r"(できない|してはならない|禁止|認められ|使用できません|変更できません"
    r"|以内|未満|以上|最小限|最も|なるべく|運用負荷|コスト効率"
    r"|[0-9]+\s*(分|時間|日|か月|年|TB|GB|MB|ミリ秒|%|件|台|アカウント|インスタンス))")


def c1_2_constraints(off, mine):
    """C1-2 問題文に、絞り込みに使う制約が2つ以上あるか"""
    def n(q):
        return len(set(CONSTRAINT.findall(q.get("question", ""))))
    o = sum(1 for q in off if n(q) >= 2) * 100 // len(off)
    m = sum(1 for q in mine if n(q) >= 2) * 100 // len(mine)
    return m >= o - 10, "制約2つ以上: 公式 %d%% / 自作 %d%%" % (o, m)


def c2_3_near_miss(off, mine):
    """C2-3 誤答の少なくとも1つが、正解と大部分同一で差分が1点だけか

    公式は「正解とほぼ同じだが1箇所だけ違う」誤答を置いて、
    細部を理解していないと選べないようにしている。
    """
    from difflib import SequenceMatcher

    def has(q):
        cor = [o.get("text", "") for o in q["options"] if o.get("correct")]
        wrong = [o.get("text", "") for o in q["options"] if not o.get("correct")]
        if not cor or not wrong:
            return False
        return any(SequenceMatcher(None, c, w).ratio() >= 0.6 for c in cor for w in wrong)
    o = sum(1 for q in off if has(q)) * 100 // len(off)
    m = sum(1 for q in mine if has(q)) * 100 // len(mine)
    return m >= o - 10, "正解と酷似した誤答あり: 公式 %d%% / 自作 %d%%" % (o, m)


NUM_IN_OPT = re.compile(r"(\$[0-9]|[0-9]+\s*(ドル|円)|最大\s*[0-9]+\s*(個|件|TB|GB))")


def c3_7_no_price(off, mine):
    """C3-7 選択肢の本文に料金・上限値を書いていないか(公式は解説側にだけ書く)"""
    o = sum(1 for q in off for x in q["options"] if NUM_IN_OPT.search(x.get("text", "")))
    m = sum(1 for q in mine for x in q["options"] if NUM_IN_OPT.search(x.get("text", "")))
    return m <= max(3, o), "選択肢に料金/上限: 公式 %d箇所 / 自作 %d箇所" % (o, m)


def c5_5_count_stated(off, mine):
    """C5-5 複数選択のとき、選ぶ数が問題文に書かれているか"""
    def bad(qs):
        out = []
        for q in qs:
            nc = q.get("n_correct") or sum(1 for x in q["options"] if x.get("correct"))
            if nc < 2:
                continue
            if not re.search(r"(2|3|二|三|２|３)\s*つ", q.get("question", "")):
                out.append(q.get("id", "?"))
        return out
    b = bad(mine)
    return not b, "選択数が未記載: 自作 %d問 %s" % (len(b), b[:3] if b else "")


def c6_2_three_step(off, mine):
    """C6-2 誤答の解説が「①何をする機能か → ②ただし → ③どの要件を満たさないか」の3段か"""
    TURN = re.compile(r"(ただし|しかし|ものの|一方|ため|ので|には向|は満たせ|できません|ありません)")
    def ratio(qs):
        tot = ok = 0
        for q in qs:
            for x in q["options"]:
                if x.get("correct"):
                    continue
                e = x.get("explanation") or ""
                if not e:
                    continue
                tot += 1
                # 機能の説明があり、かつ転換の接続があるか
                if len(e) >= 80 and TURN.search(e):
                    ok += 1
        return 100 * ok // max(1, tot)
    o, m = ratio(off), ratio(mine)
    return m >= o - 10, "誤答の解説が転換つき: 公式 %d%% / 自作 %d%%" % (o, m)


def c1_6_length(off, mine):
    """C1-6 問題文の長さが資格の型に合っているか"""
    bad = 0
    for ex in sorted({q["exam"] for q in mine}):
        o = sorted(len(q.get("question", "")) for q in off if q.get("exam") == ex)
        m = [len(q["question"]) for q in mine if q["exam"] == ex]
        if not o or not m:
            continue
        bad += sum(1 for x in m if x < o[int(len(o) * .1)])
    return bad == 0, "公式の下位10%%を下回る問題: %d問" % bad


# ---- チェックリスト全項目 ---------------------------------------
# (番号, 内容, 状態, 測定関数)
#   "測定" … 実装済み / "要AI" … 機械では無理 / "未実装" … 機械化できるが未着手
CRITERIA = [
    ("C0-1", "評価軸ありなら4肢とも技術的に要件を満たすか", "要AI", None),
    ("C0-2", "評価軸なしなら誤答3肢が要件違反か仕様上不可か", "要AI", None),
    ("C1-1", "問題文に登場人物と現行構成があるか", "要AI", None),
    ("C1-2", "絞り込みに使う制約が2つ以上あるか", "測定", c1_2_constraints),
    ("C1-3", "どの誤答も落とさない飾りの制約が半分以上でないか", "要AI", None),
    ("C1-4", "正解肢だけが問題文の語を再利用していないか", "測定", None),   # audit_difficulty で測定
    ("C1-5", "数値・期間が判断に効いているか", "要AI", None),
    ("C1-6", "分量が資格の型に合っているか", "測定", c1_6_length),
    ("C2-1", "4肢が軸を共有した集合になっているか", "要AI", None),
    ("C2-2", "2軸型なら片方だけ誤りの肢が両方あるか", "要AI", None),
    ("C2-3", "正解と大部分同一で差分1点の誤答があるか", "測定", c2_3_near_miss),
    ("C2-4", "正解が突出して長くないか", "測定", None),                     # audit_difficulty で測定
    ("C2-5", "手順形式なら全肢の手順数が揃っているか", "未実装", None),
    ("C2-6", "読んだ瞬間に切れる自己矛盾語の肢が2つ以上ないか", "測定", None),  # audit_difficulty で測定
    ("C2-7", "並び順から正解位置が推測できないか", "測定", None),            # audit_all で測定
    ("C2-8", "肢の数が1正解4肢/2正解5肢/3正解6肢か", "測定", None),          # audit_content で測定
    ("C3-1", "サービス名・機能名・パラメータ名がすべて実在するか", "要AI", None),
    ("C3-2", "肢に書いた動作の説明そのものが仕様として正しいか", "要AI", None),
    ("C3-3", "誤答がD1〜D6のどれか1つに特定できるか", "要AI", None),
    ("C3-4", "誤答が問題文の制約に真っ向から反していないか", "要AI", None),
    ("C3-5", "初歩的アンチパターンが2つ以上ないか", "要AI", None),
    ("C3-6", "誤答が正解の上位/下位互換になっていないか", "要AI", None),
    ("C3-7", "選択肢本文に料金・上限値を書いていないか", "測定", c3_7_no_price),
    ("C4-1", "評価軸が問題文の事実と結びついているか", "要AI", None),
    ("C4-2", "軸を消したら正解が変わるか(軸が効いているか)", "要AI", None),
    ("C4-3", "2軸を同時に課していないか", "未実装", None),
    ("C4-4", "絶対額でなく機構で判定できるか", "要AI", None),
    ("C5-1", "複数選択がM1/M2/M3のどれかの型か", "要AI", None),
    ("C5-2", "各サブ軸に誤答が1つ以上あるか", "要AI", None),
    ("C5-3", "正解が独立に判定できるか", "要AI", None),
    ("C5-4", "誤答が1軸に固まっていないか", "要AI", None),
    ("C5-5", "選択する数が問題文に明記されているか", "測定", c5_5_count_stated),
    ("C6-1", "正解の解説が「なぜ正しいか＋なぜ他より優れるか」か", "要AI", None),
    ("C6-2", "誤答の解説が3段構成か", "測定", c6_2_three_step),
    ("C6-3", "理由のない「不正解です」がないか", "測定", None),              # audit_consistency で測定
    ("C6-4", "テキストを変えたら解説を整合させたか", "測定", None),          # 作業時に verify で確認
    ("C6-5", "解説の仕様が実在し正しいか", "要AI", None),
]


def main():
    off, mine = load()
    print("=" * 78)
    print(" チェックリスト37項目の充足状況")
    print(" 出典: 資料/生成/_review_criteria.md（公式61問の精読から導出）")
    print("=" * 78)
    print()

    ng = 0
    counts = {"測定": 0, "要AI": 0, "未実装": 0}
    for num, text, kind, fn in CRITERIA:
        counts[kind] += 1
        if fn:
            ok, note = fn(off, mine)
            if not ok:
                ng += 1
            print("  %-5s %-6s %-44s %s" % (num, "OK" if ok else "要確認", text, note))
        else:
            mark = {"測定": "他で測定", "要AI": "要AI/人", "未実装": "未実装"}[kind]
            print("  %-5s %-6s %-44s" % (num, mark, text))

    print()
    print("-" * 78)
    print("  機械で測定: %d項目 / AIか人の判断が要る: %d項目 / 機械化できるが未実装: %d項目"
          % (counts["測定"], counts["要AI"], counts["未実装"]))
    print()
    print("  **37項目のうち %d項目は機械では判定できない。**" % counts["要AI"])
    print("  機械の検査が全部通っても、問題の質は保証されない。")
    print("  定期的に、公式問題と混ぜた出典を伏せた判定を行うこと（過去2回実施）。")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
