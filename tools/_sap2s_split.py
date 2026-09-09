# -*- coding: utf-8 -*-
"""加筆せず、連用中止を句点に替えるだけで2文にする（語彙集合を1語も動かさない方式）。

「XをAし、YをBする。」-> 「XをAする。YをBする。」
重なり(Jaccard)は語彙集合が同じなら原理的に動かない。長さも +1字程度。
"""
import json, glob, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]

# 連用中止（〜し、／〜して、）の直前が動詞語幹になっているところ
# 「〜せず、」「〜でなく、」等の否定・並列は割らない
CAND = re.compile(r"(?P<stem>[一-龥ァ-ヶーA-Za-z0-9)）]{2,})(?P<mid>させて|させ|して|し)、")
NG_PREV = ("ず", "ない", "なく", "もし", "ただ")

def splits(t):
    """割れる位置を（開始, 終了, 置換後）で返す"""
    out = []
    for m in CAND.finditer(t):
        stem, mid = m.group("stem"), m.group("mid")
        if stem.endswith(NG_PREV):
            continue
        rep = {"し": "する。", "して": "する。", "させ": "させる。", "させて": "させる。"}[mid]
        out.append((m.start("mid"), m.end() , rep))
    return out

def apply_split(t, k=1):
    """後ろからではなく、文が均等に割れる位置を優先して k 箇所で割る"""
    cands = splits(t)
    if not cands:
        return None
    # 文の中央に最も近い位置を選ぶ（前後が極端に短い分割を避ける）
    mid = len(t) / 2
    cands.sort(key=lambda c: abs(c[0] - mid))
    use = sorted(cands[:k])
    out, prev = [], 0
    for s, e, rep in use:
        out.append(t[prev:s]); out.append(rep); prev = e
    out.append(t[prev:])
    r = "".join(out)
    return r

def main():
    qs = []
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SAP-C02_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            q["_f"] = Path(f).name; qs.append(q)
    ok_q, part_q, no_q = [], [], []
    for q in qs:
        ones = [o for o in q["options"] if len(sent(o["text"])) < 2]
        if not ones:
            continue
        res = {o["letter"]: apply_split(o["text"]) for o in ones}
        good = {L: r for L, r in res.items()
                if r and len(sent(r)) >= 2 and set(WORD.findall(r)) == set(WORD.findall(
                    next(o["text"] for o in q["options"] if o["letter"] == L)))}
        if len(good) == len(ones):
            ok_q.append((q, good))
        elif good:
            part_q.append((q, good, len(ones)))
        else:
            no_q.append(q)
    n = sum(len(q["options"]) for q in qs)
    two = sum(1 for q in qs for o in q["options"] if len(sent(o["text"])) >= 2)
    add = sum(len(g) for _, g in ok_q)
    print("全肢を加筆なしで割れる問題: %d問 / %d肢" % (len(ok_q), add))
    print("一部の肢しか割れない問題  : %d問（割れる肢 %d / 1文肢 %d）"
          % (len(part_q), sum(len(g) for _, g, _ in part_q), sum(t for _, _, t in part_q)))
    print("1肢も割れない問題        : %d問" % len(no_q))
    print()
    print("複文率: 現在 %d/%d = %.1f%% -> 全肢可の問題だけ割ると %d/%d = %.1f%% (公式 84.7%%)"
          % (two, n, 100*two/n, two+add, n, 100*(two+add)/n))
    tot_part = sum(len(g) for _, g, _ in part_q)
    print("        一部可も含めて割ると %d/%d = %.1f%%" % (two+add+tot_part, n, 100*(two+add+tot_part)/n))
    if "--list" in sys.argv:
        print()
        for q, g in ok_q:
            print("=== %s (%s) 全%d肢中 %d肢を分割" % (q["id"], q["_f"], len(q["options"]), len(g)))
            for o in q["options"]:
                if o["letter"] in g:
                    print("  %s%s 旧: %s" % (o["letter"], "*" if o["correct"] else " ", o["text"]))
                    print("     新: %s" % g[o["letter"]])
        print()
        print("---- 一部しか割れない問題 ----")
        for q, g, t in part_q:
            print("=== %s (%s) 1文肢%d のうち %d肢のみ分割可: %s" % (q["id"], q["_f"], t, len(g), ",".join(sorted(g))))
        print("---- 1肢も割れない問題 ----")
        for q in no_q: print("=== %s (%s)" % (q["id"], q["_f"]))
    return ok_q, part_q, no_q

if __name__ == "__main__":
    main()
