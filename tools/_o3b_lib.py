# -*- coding: utf-8 -*-
"""CLF-C02 / SOA-C03 の O-3(正解と酷似した誤答)是正 用の共通ライブラリ。
tools/_deao3_lib.py を資格パラメータ化したもの。測り方は同一
(difflib.SequenceMatcher(正解肢text, 誤答肢text).ratio() の全ペア最大値、閾値0.72)。
公式比較は必ず同一資格の公式問題とだけ行う(鉄則5: 資格をまたいで基準を作らない)。
"""
import json, re, statistics
from pathlib import Path
from difflib import SequenceMatcher
from itertools import combinations

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

# 測定対象ファイル。mixed_orig_b1.json は他資格と同居しているため
# 「読むが書かない」(WRITABLE から除外) 扱いにする(鉄則7: 同じファイルを複数作業で触らない)。
EXAMS = {
    "CLF-C02": dict(
        files=["CLF-C02_orig.json", "CLF-C02_orig_b2.json", "CLF-C02_orig_b3.json",
               "CLF-C02_orig_b4.json", "CLF-C02_orig_gap1.json", "CLF-C02_orig_topic1.json"],
        readonly=[]),
    "SOA-C03": dict(
        files=["SOA-C03_orig.json", "SOA-C03_orig_b2.json", "SOA-C03_orig_b3.json",
               "SOA-C03_orig_b4.json", "SOA-C03_orig_b5.json", "SOA-C03_orig_gap1.json",
               "SOA-C03_orig_multi1.json", "SOA-C03_orig_topic1.json"],
        readonly=["mixed_orig_b1.json"]),
}


def files_of(exam):
    c = EXAMS[exam]
    return c["files"], c["readonly"]


def load_mine(exam):
    qs = []
    w, ro = files_of(exam)
    for f in w + ro:
        for q in json.load(open(GEN / f, encoding="utf-8")):
            if q.get("exam") != exam:
                continue
            q["_file"] = f
            q["_ro"] = f in ro
            qs.append(q)
    return qs


def load_off(exam):
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")
            and q.get("exam") == exam]


def pairs(q):
    cor = [o for o in q["options"] if o.get("correct")]
    wr = [o for o in q["options"] if not o.get("correct")]
    out = [(SequenceMatcher(None, c["text"], w["text"]).ratio(), w.get("letter"), c.get("letter"))
           for c in cor for w in wr]
    return sorted(out, reverse=True)


def maxsim(q):
    p = pairs(q)
    return p[0][0] if p else None


def allpair_mean(q):
    t = [o["text"] for o in q["options"]]
    v = [SequenceMatcher(None, a, b).ratio() for a, b in combinations(t, 2)]
    return statistics.mean(v) if v else None


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
    return (100.0*hi/t, 100.0*lo/t) if t else (0.0, 0.0)


def metrics(qs):
    ch = [q for q in qs if q.get("type", "choice") == "choice" and q.get("options")]
    ms = [m for m in (maxsim(q) for q in ch) if m is not None]
    ov = [o for o in (overlap(q) for q in ch) if o is not None]
    ap = [a for a in (allpair_mean(q) for q in ch) if a is not None]
    mm = sum(multi_sent(q)[0] for q in ch); mt = sum(multi_sent(q)[1] for q in ch)
    ln = [len(o["text"]) for q in ch for o in q["options"]]
    ql = [len(q["question"]) for q in ch]
    ex = [len(o.get("explanation") or "") for q in ch for o in q["options"]]
    hi, lo2 = longest(ch)
    return dict(n=len(ms),
                o3=100.0*sum(1 for m in ms if m >= .72)/len(ms),
                s60=100.0*sum(1 for m in ms if m >= .60)/len(ms),
                lo=100.0*sum(1 for m in ms if m < .50)/len(ms),
                med=statistics.median(ms), ov=statistics.mean(ov),
                ap=statistics.mean(ap), spike=statistics.mean(ms)-statistics.mean(ap),
                fk=100.0*mm/mt, optlen=statistics.median(ln), qlen=statistics.median(ql),
                exlen=statistics.median(ex), hi=hi, lo3=lo2)


LABELS = [("n", "問題数", "%8d"), ("o3", "O-3(>=0.72)", "%7.1f%%"), ("s60", ">=0.60", "%7.1f%%"),
          ("lo", "<0.50", "%7.1f%%"), ("med", "最大類似の中央", "%8.3f"),
          ("ap", "全ペア平均", "%8.3f"), ("spike", "突出度", "%8.3f"),
          ("ov", "肢の語の重なり", "%8.3f"), ("fk", "選択肢2文以上", "%7.1f%%"),
          ("optlen", "選択肢の中央字数", "%8.0f"), ("qlen", "問題文の中央字数", "%8.0f"),
          ("exlen", "解説の中央字数", "%8.0f"),
          ("hi", "最長が正解", "%7.1f%%"), ("lo3", "最長が誤答", "%7.1f%%")]


def show(cols):
    """cols = [(見出し, metrics dict), ...]"""
    print("%-18s" % "指標" + "".join("%9s" % c[0] for c in cols))
    for k, lab, f in LABELS:
        print("%-18s" % lab + "".join((f % c[1][k]) for c in cols))


if __name__ == "__main__":
    import sys
    for ex in (sys.argv[1:] or ["CLF-C02", "SOA-C03"]):
        print("=== %s ===" % ex)
        show([("公式", metrics(load_off(ex))), ("自作", metrics(load_mine(ex)))])
        print()
