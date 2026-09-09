# -*- coding: utf-8 -*-
"""SAP-C02 / AIP-C01 の O-3(正解と酷似した誤答)是正 用の共通ライブラリ。
_deao3_lib.py を資格パラメータ化したもの。測り方は同一(SequenceMatcher)。
公式比較は必ず同一資格の公式問題とだけ行う(鉄則5: 資格をまたいで基準を作らない)。

対象は SAP-C02 と AIP-C01 のみ。他資格のファイルは読まない。
"""
import json, re, statistics, os
from pathlib import Path
from difflib import SequenceMatcher
from itertools import combinations

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
FILESET = {
    "SAP-C02": ["SAP-C02_orig.json", "SAP-C02_orig_b2.json", "SAP-C02_orig_b3.json",
                "SAP-C02_orig_b4.json", "SAP-C02_orig_multi1.json"],
    "AIP-C01": ["AIP-C01_orig_b2.json", "AIP-C01_orig_b3.json", "AIP-C01_orig_b4.json",
                "AIP-C01_orig_b5.json", "AIP-C01_orig_topic1.json", "AIP-C01_orig_topic2.json",
                "AIP-C01_orig_topic3.json", "AIP-C01_orig_topic4.json"],
}
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def exam():
    ex = os.environ.get("O3EXAM", "")
    if ex not in FILESET:
        raise SystemExit("環境変数 O3EXAM に SAP-C02 か AIP-C01 を指定してください")
    return ex


def files(ex=None):
    return FILESET[ex or exam()]


def load_mine(ex=None):
    ex = ex or exam()
    qs = []
    for f in FILESET[ex]:
        for q in json.load(open(GEN / f, encoding="utf-8")):
            q["_file"] = f
            qs.append(q)
    return qs


def load_off(ex=None):
    ex = ex or exam()
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")
            and q.get("exam") == ex]


def pairs(q):
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
    n = m = 0
    for o in q["options"]:
        n += 1
        if len(sentences(o.get("text", ""))) >= 2:
            m += 1
    return m, n


def report(qs, label):
    ch = [q for q in qs if q.get("type", "choice") == "choice" and q.get("options")]
    ms = [m for m in (maxsim(q) for q in ch) if m is not None]
    ov = [o for o in (overlap(q) for q in ch) if o is not None]
    mm = sum(multi_sent(q)[0] for q in ch); mt = sum(multi_sent(q)[1] for q in ch)
    r = lambda th: 100 * sum(1 for m in ms if m >= th) / len(ms)
    print("%-12s n=%3d | O-3(>=0.72) %5.1f%% | >=0.60 %5.1f%% | <0.50 %5.1f%% | 中央 %.3f | 重なり %.3f | 複文 %4.1f%%"
          % (label, len(ms), r(.72), r(.60), 100 * sum(1 for m in ms if m < .50) / len(ms),
             statistics.median(ms), statistics.mean(ov), 100 * mm / mt))
    return dict(n=len(ms), o3=r(.72), s60=r(.60), lo=100*sum(1 for m in ms if m<.50)/len(ms),
                med=statistics.median(ms), ov=statistics.mean(ov), fk=100*mm/mt)


if __name__ == "__main__":
    for ex in ("SAP-C02", "AIP-C01"):
        report(load_off(ex), ex + " 公式")
        report(load_mine(ex), ex + " 自作")
