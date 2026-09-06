# -*- coding: utf-8 -*-
"""AIP-C01 自前実装型誤答の是正用 計測。 python tools/_aipself_measure.py [--list]"""
import json, re, sys, glob, os, statistics
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(BASE, "資料", "生成")
WORD = re.compile(r'[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}')

# 指定8語（本命）
PATS_CORE = ["自前で", "自社で実装", "独自に開発", "カスタムスクリプトを作成",
             "自作の", "スクラッチで", "手動で", "手作業で"]
# 広めの検出（同義の言い換え）
PATS_WIDE = PATS_CORE + [
    "自前", "自社で開発", "自社開発", "独自に実装", "独自実装", "内製",
    "カスタムスクリプト", "カスタムコードを", "スクラッチ", "一から", "ゼロから",
    "手動", "手作業", "人手で", "自作", "自ら実装", "独自のスクリプト",
    "独自のコード", "自前実装",
]


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
    best = 0.0
    for o in q["options"]:
        if o.get("correct"):
            continue
        for c in cor:
            r = SequenceMatcher(None, c, o["text"]).ratio()
            best = max(best, r)
    return best


def overlap(q):
    s = [set(WORD.findall(o["text"])) for o in q["options"]]
    s = [x for x in s if x]
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else None


def longest_correct(q):
    m = max(q["options"], key=lambda o: len(o["text"]))
    return bool(m.get("correct"))


def selfhits(qs, pats):
    hits = []
    for q in qs:
        for o in q["options"]:
            if o.get("correct"):
                continue
            m = [p for p in pats if p in o["text"]]
            if m:
                hits.append((q["_file"], q["id"], o["letter"], m, o["text"]))
    return hits


def main():
    qs = load()
    n = len(qs)
    nwrong = sum(1 for q in qs for o in q["options"] if not o.get("correct"))
    ov = statistics.mean([overlap(q) for q in qs if overlap(q) is not None])
    h85 = sum(1 for q in qs if maxsim(q) >= 0.85)
    lc = sum(1 for q in qs if longest_correct(q))
    core = selfhits(qs, PATS_CORE)
    wide = selfhits(qs, PATS_WIDE)
    out = []
    out.append(f"問数 {n} / 誤答肢 {nwrong}")
    out.append(f"1. 語の重なり {ov:.3f}  (目標 0.22-0.27)")
    out.append(f"2. 類似0.85以上 {h85}問 {100*h85/n:.1f}%  (目標 8-14%)")
    out.append(f"3. 最長が正解 {lc}問 {100*lc/n:.1f}%  (目標 22-32%)")
    out.append(f"4. 自前実装型(指定8語) {len(core)}肢/{len(set(h[1] for h in core))}問 "
               f"{100*len(core)/nwrong:.1f}%  (目標 1.0%以下)")
    out.append(f"   自前実装型(広義) {len(wide)}肢/{len(set(h[1] for h in wide))}問 "
               f"{100*len(wide)/nwrong:.1f}%")
    print("\n".join(out))
    if "--list" in sys.argv:
        print("\n--- 広義ヒット ---")
        for f, i, l, m, t in wide:
            print(f"[{i}] {l} {','.join(m)} :: {t[:110]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
