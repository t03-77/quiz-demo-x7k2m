# -*- coding: utf-8 -*-
"""AIP-C01 の「双子の肢」4指標を測る。 python tools/_twin_measure.py [--dump]"""
import json, re, sys, glob, os, statistics
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(BASE, "資料", "生成")
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')
TERM = re.compile(r"[A-Z][A-Za-z0-9]{2,}(?:\s+[A-Z][A-Za-z0-9]+){0,2}")
COMMON = {"AWS", "Amazon", "The", "This", "IAM", "VPC", "API", "EC2", "S3"}


def load(pat="AIP-C01_orig*.json"):
    qs = []
    for f in sorted(glob.glob(os.path.join(GEN, pat))):
        if "_bak" in f:
            continue
        d = json.load(open(f, encoding="utf-8"))
        for q in (d.get("questions", d) if isinstance(d, dict) else d):
            q["_file"] = os.path.basename(f)
            qs.append(q)
    return qs


def maxsim(q):
    cor = [o["text"] for o in q["options"] if o.get("correct")]
    best = (0.0, None)
    for o in q["options"]:
        if o.get("correct"):
            continue
        for c in cor:
            r = SequenceMatcher(None, c, o["text"]).ratio()
            if r > best[0]:
                best = (r, o.get("letter"))
    return best


def simfor(q, letter):
    cor = [o["text"] for o in q["options"] if o.get("correct")]
    t = [o["text"] for o in q["options"] if o.get("letter") == letter][0]
    return max(SequenceMatcher(None, c, t).ratio() for c in cor)


def overlap(q):
    s = [set(WORD.findall(o["text"])) for o in q["options"]]
    s = [x for x in s if x]
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def longest_correct(q):
    m = max(q["options"], key=lambda o: len(o["text"]))
    return bool(m.get("correct"))


def kwleak(q):
    qt = {m.group(0) for m in TERM.finditer(q.get("question", ""))} - COMMON
    if not qt:
        return False
    cor = " ".join(o["text"] for o in q["options"] if o.get("correct"))
    wrong = " ".join(o["text"] for o in q["options"] if not o.get("correct"))
    hit = {t for t in qt if t in cor}
    return bool(hit) and not any(t in wrong for t in hit)


def main():
    qs = load()
    n = len(qs)
    sims = [(q["id"], *maxsim(q)) for q in qs]
    h85 = [s for s in sims if s[1] >= 0.85]
    h72 = [s for s in sims if s[1] >= 0.72]
    h92 = [s for s in sims if s[1] >= 0.92]
    ov = statistics.mean([overlap(q) for q in qs if overlap(q) is not None])
    lc = sum(1 for q in qs if longest_correct(q))
    kl = [q["id"] for q in qs if kwleak(q)]
    print(f"問数 {n}")
    print(f"類似0.72以上 {len(h72)}問 {100*len(h72)/n:.1f}%")
    print(f"類似0.85以上 {len(h85)}問 {100*len(h85)/n:.1f}%   (目標 10-14%)")
    print(f"類似0.92以上 {len(h92)}問 {100*len(h92)/n:.1f}%")
    print(f"語の重なり {ov:.3f}   (目標 0.22-0.27)")
    print(f"最長が正解 {lc}問 {100*lc/n:.1f}%   (目標 20-30%)")
    print(f"キーワード直結 {len(kl)}問 {kl}")
    if "--dump" in sys.argv:
        for i, s in enumerate(sorted(h85, key=lambda x: -x[1])):
            print(f"  {i+1:2d} {s[0]} {s[2]} {s[1]:.3f}")


if __name__ == "__main__":
    main()
