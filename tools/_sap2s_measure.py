# -*- coding: utf-8 -*-
"""SAP-C02 複文率(選択肢が2文以上)の測定。公式との比較・正解/誤答別の内訳も出す。"""
import json, re, statistics, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
EXAM = "SAP-C02"

def load_src():
    qs = []
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SAP-C02_orig*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        arr = d.get("questions", d) if isinstance(d, dict) else d
        for q in arr:
            q["_file"] = Path(f).name
        qs += [q for q in arr if q.get("exam") == EXAM]
    return qs

def load_off():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    return [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options") and q.get("exam") == EXAM]

def sentences(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]

WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

def stats(qs, label, verbose=True):
    ns, nc, nw, c2, w2 = [], 0, 0, 0, 0
    lens = []
    for q in qs:
        for o in q.get("options") or []:
            t = (o.get("text") or "").strip()
            if not t:
                continue
            k = len(sentences(t))
            ns.append(k)
            lens.append(len(t))
            if o.get("correct"):
                nc += 1
                c2 += (k >= 2)
            else:
                nw += 1
                w2 += (k >= 2)
    two = 100 * sum(1 for x in ns if x >= 2) / max(1, len(ns))
    vals = []
    for q in qs:
        sets = [set(WORD.findall(o.get("text", ""))) for o in (q.get("options") or []) if o.get("text")]
        sets = [s for s in sets if s]
        if len(sets) < 2:
            continue
        pr = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                u = sets[i] | sets[j]
                if u:
                    pr.append(len(sets[i] & sets[j]) / len(u))
        if pr:
            vals.append(statistics.mean(pr))
    ov = statistics.mean(vals) if vals else 0
    thin = 100 * sum(1 for v in vals if v < 0.1) / max(1, len(vals))
    hi = lo = same = 0
    for q in qs:
        op = q.get("options") or []
        cor = [len(o["text"]) for o in op if o.get("correct")]
        wr = [len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr:
            continue
        m = max(cor + wr)
        a = max(cor) == m
        b = max(wr) == m
        if a and not b: hi += 1
        elif b and not a: lo += 1
        else: same += 1
    t = hi + lo + same
    if verbose:
        print("%-11s Q=%-4d 肢=%-5d 2文以上=%5.1f%% (正解肢 %5.1f%% [%d/%d] / 誤答肢 %5.1f%% [%d/%d])"
              % (label, len(qs), len(ns), two, 100*c2/max(1,nc), c2, nc, 100*w2/max(1,nw), w2, nw))
        print("            重なり=%.3f 薄い問題=%4.1f%%  最長が正解=%5.1f%% 最長が誤答=%5.1f%%  肢の中央長=%d"
              % (ov, thin, 100*hi/max(1,t), 100*lo/max(1,t), statistics.median(lens)))
    return {"two": two, "ov": ov, "hi": 100*hi/max(1,t), "lo": 100*lo/max(1,t),
            "c2": c2, "nc": nc, "w2": w2, "nw": nw, "n": len(ns), "thin": thin,
            "medlen": statistics.median(lens)}

if __name__ == "__main__":
    o = stats(load_off(), "公式SAP")
    m = stats(load_src(), "自作SAP")
    print()
    print("目標(公式の75〜125%%): %.1f%% 〜 %.1f%%" % (o["two"]*0.75, o["two"]*1.25))
    need = int((o["two"]/100) * m["n"] + 0.9999)
    have = m["c2"] + m["w2"]
    print("公式水準(%.1f%%)にするには 肢 %d/%d が2文以上。現在 %d。あと %d肢"
          % (o["two"], need, m["n"], have, need - have))
