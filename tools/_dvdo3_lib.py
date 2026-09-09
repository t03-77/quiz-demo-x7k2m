# -*- coding: utf-8 -*-
"""DVA-C02 / DOP-C02 の O-3(正解と酷似した誤答)是正 用の共通ライブラリ。
tools/_deao3_lib.py を資格切替できるようにしたもの（測り方は完全に同一）。
公式比較は必ず同じ資格の公式問題とだけ行う(鉄則5)。

資格の指定: 環境変数 O3EXAM、または import 後に set_exam() を呼ぶ。
"""
import json, os, re, statistics
from pathlib import Path
from difflib import SequenceMatcher
from itertools import combinations

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

FILES_BY_EXAM = {
    "DVA-C02": ["DVA-C02_orig.json", "DVA-C02_orig_b2.json", "DVA-C02_orig_b3.json",
                "DVA-C02_orig_b4.json", "DVA-C02_orig_gap1.json", "DVA-C02_orig_topic1.json"],
    "DOP-C02": ["DOP-C02_orig.json", "DOP-C02_orig_b2.json", "DOP-C02_orig_b3.json",
                "DOP-C02_orig_b4.json", "DOP-C02_orig_b5.json", "DOP-C02_orig_gap1.json",
                "DOP-C02_orig_multi1.json"],
}

EXAM = os.environ.get("O3EXAM", "DVA-C02")
if EXAM not in FILES_BY_EXAM:
    raise SystemExit("O3EXAM は DVA-C02 / DOP-C02 のみ: %r" % EXAM)
FILES = FILES_BY_EXAM[EXAM]


def set_exam(ex):
    global EXAM, FILES
    if ex not in FILES_BY_EXAM:
        raise SystemExit("対象外の資格: %r（DVA-C02/DOP-C02 のみ）" % ex)
    EXAM, FILES = ex, FILES_BY_EXAM[ex]


def load_mine():
    qs = []
    for f in FILES:
        for q in json.load(open(GEN / f, encoding="utf-8")):
            if q.get("exam") != EXAM:
                raise SystemExit("中断: %s に %s 以外の問題 (%s)" % (f, EXAM, q.get("exam")))
            q["_file"] = f
            qs.append(q)
    return qs


def load_off():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")
            and q.get("exam") == EXAM]


def pairs(q):
    """[(sim, wrong_letter, correct_letter)] を降順で返す"""
    cor = [o for o in q["options"] if o.get("correct")]
    wr = [o for o in q["options"] if not o.get("correct")]
    out = [(SequenceMatcher(None, c["text"], w["text"]).ratio(), w.get("letter"), c.get("letter"))
           for c in cor for w in wr]
    return sorted(out, reverse=True)


def maxsim(q):
    p = pairs(q)
    return p[0][0] if p else None


def allpair_mean(q):
    op = [o for o in q["options"] if o.get("text")]
    ps = [SequenceMatcher(None, a["text"], b["text"]).ratio() for a, b in combinations(op, 2)]
    return statistics.mean(ps) if ps else None


def overlap(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    ps = [len(a & b) / len(a | b) for a, b in combinations(s, 2) if a | b]
    return statistics.mean(ps) if ps else None


def sentences(t):
    return [x for x in re.split(r"(?<=[。？！])", t or "") if x.strip()]


def multi_sent(q):
    n = m = 0
    for o in q["options"]:
        n += 1
        if len(sentences(o.get("text", ""))) >= 2:
            m += 1
    return m, n


def longest(qs):
    hi = lo = same = 0
    for q in qs:
        op = q.get("options") or []
        cor = [len(o["text"]) for o in op if o.get("correct")]
        wr = [len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr:
            continue
        m = max(cor + wr); a = max(cor) == m; b = max(wr) == m
        if a and not b: hi += 1
        elif b and not a: lo += 1
        else: same += 1
    t = hi + lo + same
    return 100 * hi / t, 100 * lo / t


def metrics(qs):
    ch = [q for q in qs if q.get("type", "choice") == "choice" and q.get("options")]
    ms = [m for m in (maxsim(q) for q in ch) if m is not None]
    ov = [o for o in (overlap(q) for q in ch) if o is not None]
    ap = [a for a in (allpair_mean(q) for q in ch) if a is not None]
    mm = sum(multi_sent(q)[0] for q in ch); mt = sum(multi_sent(q)[1] for q in ch)
    ln = [len(o["text"]) for q in ch for o in q["options"]]
    qn = [len(q["question"]) for q in ch]
    ex = [len(o.get("explanation") or "") for q in ch for o in q["options"]]
    hi, lo2 = longest(ch)
    return dict(n=len(ms),
                o3=100 * sum(1 for m in ms if m >= .72) / len(ms),
                s60=100 * sum(1 for m in ms if m >= .60) / len(ms),
                lo=100 * sum(1 for m in ms if m < .50) / len(ms),
                med=statistics.median(ms), ov=statistics.mean(ov),
                apm=statistics.mean(ap), fk=100 * mm / mt,
                optlen=statistics.median(ln), qlen=statistics.median(qn),
                exlen=statistics.median(ex), hi=hi, lo3=lo2)


LABELS = [("n", "問数", "%8d"), ("o3", "O-3(>=0.72)", "%7.1f%%"), ("s60", ">=0.60", "%7.1f%%"),
          ("lo", "<0.50", "%7.1f%%"), ("med", "最大類似の中央", "%8.3f"),
          ("apm", "全ペア平均", "%8.3f"), ("ov", "肢の語の重なり", "%8.3f"),
          ("fk", "選択肢2文以上", "%7.1f%%"), ("optlen", "選択肢の中央字数", "%8.0f"),
          ("qlen", "問題文の中央字数", "%8.0f"), ("exlen", "解説の中央字数", "%8.0f"),
          ("hi", "最長が正解", "%7.1f%%"), ("lo3", "最長が誤答", "%7.1f%%")]


if __name__ == "__main__":
    for ex in ("DVA-C02", "DOP-C02"):
        set_exam(ex)
        O, M = metrics(load_off()), metrics(load_mine())
        print("=== %s ===" % ex)
        print("%-18s %9s %9s" % ("指標", "公式", "自作"))
        for k, lab, f in LABELS:
            print(("%-18s " + f + " " + f) % (lab, O[k], M[k]))
        print("  重なり下限(公式x0.9)=%.4f 上限(x1.1)=%.4f / 自作=%.4f"
              % (O["ov"] * 0.9, O["ov"] * 1.1, M["ov"]))
        print()
