# -*- coding: utf-8 -*-
"""AIP-C01 最終作業（制約裏返し3問 + 重なりが薄い問題）の計測。
測り方は audit_pattern.py / _sao3_lib.py と同一の定義を使う（鉄則5）。
使い方: python -X utf8 tools/_aipfin_measure.py [id ...]
"""
import json, re, statistics, sys
from pathlib import Path
from difflib import SequenceMatcher
from itertools import combinations
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sao3_lib import load_mine, load_off, WORD, sentences

EX = "AIP-C01"

def ovq(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    ps = [len(a & b) / len(a | b) for a, b in combinations(s, 2) if a | b]
    return statistics.mean(ps) if ps else None

def maxsim(q):
    cor = [o for o in q["options"] if o.get("correct")]
    wr = [o for o in q["options"] if not o.get("correct")]
    v = [SequenceMatcher(None, c["text"], w["text"]).ratio() for c in cor for w in wr]
    return max(v) if v else None

def hilo(q):
    op = q["options"]
    cor = [len(o["text"]) for o in op if o.get("correct")]
    wr = [len(o["text"]) for o in op if not o.get("correct")]
    if not cor or not wr: return None
    m = max(cor + wr); a = max(cor) == m; b = max(wr) == m
    return "hi" if (a and not b) else ("lo" if (b and not a) else "same")

TERM = re.compile(r"[A-Z][A-Za-z0-9]{2,}(?:\s+[A-Z][A-Za-z0-9]+){0,2}")
COMMON = {"AWS", "Amazon", "The", "This", "IAM", "VPC", "API", "EC2", "S3"}

def kwleak(q):
    qt = {m.group(0) for m in TERM.finditer(q.get("question", ""))} - COMMON
    if not qt: return False
    cor = " ".join(o.get("text", "") for o in q["options"] if o.get("correct"))
    wrong = " ".join(o.get("text", "") for o in q["options"] if not o.get("correct"))
    hit = {t for t in qt if t in cor}
    return bool(hit) and not any(t in wrong for t in hit)

def summary(qs, label):
    ovs = [v for v in (ovq(q) for q in qs) if v is not None]
    ms = [v for v in (maxsim(q) for q in qs) if v is not None]
    hl = [hilo(q) for q in qs]
    ns = [len(sentences(o.get("text", ""))) for q in qs for o in q["options"] if o.get("text")]
    ln = [len(o["text"]) for q in qs for o in q["options"] if o.get("text")]
    thin = sum(1 for v in ovs if v < 0.1)
    print("%-10s n=%3d | 重なり %.4f | 薄い %2d問 %4.1f%%(表示%d%%) | O-3 %4.1f%% | 複文 %4.1f%% | hi %4.1f%% lo %4.1f%% same %4.1f%% | 肢中央字数 %d | kwleak %d"
          % (label, len(qs), statistics.mean(ovs), thin, 100*thin/len(ovs), 100*thin//len(ovs),
             100*sum(1 for m in ms if m >= .72)/len(ms),
             100*sum(1 for x in ns if x >= 2)/len(ns),
             100*hl.count("hi")/len(hl), 100*hl.count("lo")/len(hl), 100*hl.count("same")/len(hl),
             int(statistics.median(ln)), sum(1 for q in qs if kwleak(q))))

if __name__ == "__main__":
    mine = [q for q in load_mine(EX)]
    off = load_off(EX)
    summary(off, "公式")
    summary(mine, "自作")
    ids = [a for a in sys.argv[1:]]
    if ids:
        idx = {q["id"]: q for q in mine}
        print()
        print("%-22s %6s %6s %-5s %s" % ("id", "重なり", "O-3sim", "hi/lo", "kwleak"))
        for i in ids:
            q = idx["AIP-C01_orig_" + i] if not i.startswith("AIP") else idx[i]
            print("%-22s %6.4f %6.3f %-5s %s" % (q["id"], ovq(q), maxsim(q), hilo(q), kwleak(q)))
