# -*- coding: utf-8 -*-
"""問題バンクの品質を公式問題と比較して定量評価する。

「本番に近いか」を主観でなく数字で見るための指標:
- 問題文の長さ分布(短すぎる=一問一答の疑い)
- 選択肢の長さ(短い誤答=捨て選択肢の疑い)
- 条件句("最も〜")の有無(選定を迫る本番型か)
- 重複・類似問題(独立生成したので衝突しうる)
"""
import json
import re
import statistics as st
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load_orig():
    js = (BASE / "data" / "orig.js").read_text(encoding="utf-8")
    return json.loads(js[js.index("["):js.rindex("]") + 1])


def load_official():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    return [q for q in d["questions"] if q["set"] in ("exam", "pretest") and q["type"] == "choice"]


COND = re.compile(r"(最も|最小限|最適|どのソリューション|どの組み合わせ|要件を満たす|コスト効率|運用上のオーバーヘッド|運用負荷)")


def profile(qs, label):
    ql = [len(q["question"]) for q in qs]
    ol, nopt, cond = [], [], 0
    for q in qs:
        opts = q.get("options") or []
        if not opts:
            continue
        nopt.append(len(opts))
        ol += [len(o["text"]) for o in opts]
        if COND.search(q["question"]):
            cond += 1
    print(f"\n■ {label}  n={len(qs)}")
    print(f"  問題文    中央値{int(st.median(ql))}字 / 平均{int(st.mean(ql))}字 / 100字未満 {sum(1 for x in ql if x < 100)}問 ({sum(1 for x in ql if x < 100)/len(ql)*100:.1f}%)")
    if ol:
        print(f"  選択肢    中央値{int(st.median(ol))}字 / 20字未満 {sum(1 for x in ol if x < 20)/len(ol)*100:.1f}%")
        print(f"  選択肢数  {dict(Counter(nopt))}")
    print(f"  条件句あり {cond/len(qs)*100:.1f}%  (「最も〜」等で選定を迫る本番型)")


def dup_check(qs):
    """同一試験内の類似問題を検出(独立生成による衝突)"""
    by_exam = defaultdict(list)
    for q in qs:
        by_exam[q["exam"]].append(q)
    hits = []
    for exam, items in by_exam.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i]["question"], items[j]["question"]
                if abs(len(a) - len(b)) > 120:
                    continue
                r = SequenceMatcher(None, a, b).ratio()
                if r > 0.72:
                    hits.append((r, items[i]["id"], items[j]["id"]))
    hits.sort(reverse=True)
    print(f"\n■ 類似問題(同一試験内, 類似度>0.72): {len(hits)}組")
    for r, x, y in hits[:12]:
        print(f"  {r:.2f}  {x} ⇔ {y}")
    return hits


orig = load_orig()
off = load_official()
profile(off, "AWS公式 模試/Pretest (基準)")
profile(orig, "オリジナル問題 (全体)")
gen = [q for q in orig if q["exam"] != "AIP-C01"]
profile(gen, "オリジナル問題 (今回生成の10資格分)")
aip = [q for q in orig if q["exam"] == "AIP-C01"]
profile(aip, "オリジナル問題 (AIP-C01 既存分)")
dup_check(gen)
