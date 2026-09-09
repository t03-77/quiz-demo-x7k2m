# -*- coding: utf-8 -*-
"""DEA-C01 の O-3(正解と酷似した誤答)是正 用の共通ライブラリ。
測り方は audit_criteria.py の c2-3 / _nm4_check.py と同じ SequenceMatcher。
公式比較は必ず DEA-C01 の公式問題とだけ行う(鉄則5: 資格をまたいで基準を作らない)。"""
import json, re, statistics
from pathlib import Path
from difflib import SequenceMatcher
from itertools import combinations

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
FILES = ["DEA-C01_orig.json", "DEA-C01_orig_b2.json", "DEA-C01_orig_b3.json",
         "DEA-C01_orig_b4.json", "DEA-C01_orig_gap1.json", "DEA-C01_orig_multi1.json"]
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def load_mine():
    qs = []
    for f in FILES:
        for q in json.load(open(GEN / f, encoding="utf-8")):
            q["_file"] = f
            qs.append(q)
    return qs


def load_off():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")
            and q.get("exam") == "DEA-C01"]


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


def overlap(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    ps = [len(a & b) / len(a | b) for a, b in combinations(s, 2) if a | b]
    return statistics.mean(ps) if ps else None


def sentences(t):
    return [x for x in re.split(r"(?<=[。？！])", t or "") if x.strip()]


def multi_sent(q):
    """選択肢が2文以上の割合を数えるための (該当肢数, 全肢数)"""
    n = m = 0
    for o in q["options"]:
        n += 1
        if len(sentences(o.get("text", ""))) >= 2:
            m += 1
    return m, n


def report(qs, label):
    ch = [q for q in qs if q.get("type", "choice") == "choice" and q.get("options")]
    ms = [maxsim(q) for q in ch]
    ms = [m for m in ms if m is not None]
    ov = [overlap(q) for q in ch]
    ov = [o for o in ov if o is not None]
    mm = sum(multi_sent(q)[0] for q in ch); mt = sum(multi_sent(q)[1] for q in ch)
    r = lambda th: 100 * sum(1 for m in ms if m >= th) / len(ms)
    print("%-10s n=%3d | O-3(>=0.72) %5.1f%% | >=0.60 %5.1f%% | <0.50 %5.1f%% | 中央 %.3f | 重なり %.3f | 複文 %4.1f%%"
          % (label, len(ms), r(.72), r(.60), 100 * sum(1 for m in ms if m < .50) / len(ms),
             statistics.median(ms), statistics.mean(ov), 100 * mm / mt))
    return dict(n=len(ms), o3=r(.72), s60=r(.60), lo=100*sum(1 for m in ms if m<.50)/len(ms),
                med=statistics.median(ms), ov=statistics.mean(ov), fk=100*mm/mt)


if __name__ == "__main__":
    report(load_off(), "DEA 公式")
    report(load_mine(), "DEA 自作")
