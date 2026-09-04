# -*- coding: utf-8 -*-
"""AIP-C01 長さ調整用の自己チェック。生成JSONを直接読む(orig.js は再ビルドしないため)。"""
import json, glob, statistics, sys, importlib.util
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
spec = importlib.util.spec_from_file_location("st", BASE / "tools" / "audit_strawman.py")
st = importlib.util.module_from_spec(spec)
sys.modules["st"] = st
src = (BASE / "tools" / "audit_strawman.py").read_text(encoding="utf-8")
ns = {}
ns["__file__"] = str(BASE / "tools" / "audit_strawman.py")
exec(compile(src.split("def main(")[0], "audit_strawman", "exec"), ns)

def load_orig():
    qs = []
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        if not isinstance(d, list): continue
        for q in d:
            if isinstance(q, dict) and q.get("exam") == "AIP-C01" and q.get("set") == "orig":
                qs.append(q)
    return qs

def overlap(q):
    """肢どうしの語の重なり(audit_pattern.py と同等の簡易版)"""
    import re
    toks = [set(re.findall(r"[A-Za-z0-9]+|[ァ-ヶー]+|[一-龥]+", o["text"])) for o in q["options"]]
    ps, n = 0.0, 0
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            u = toks[i] | toks[j]
            if u: ps += len(toks[i] & toks[j]) / len(u); n += 1
    return ps / n if n else 0.0

def main():
    qs = load_orig()
    L = sorted(len(q["question"]) for q in qs)
    off = [q for q in json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))["questions"]
           if q.get("exam") == "AIP-C01" and q.get("set") in ("exam", "pretest")]
    fm = statistics.median(sorted(len(q["question"]) for q in off))
    m = statistics.median(L)
    print(f"問題文 中央値={m:.0f} (公式{fm:.0f} 比 {m/fm*100:.0f}%) 平均={statistics.mean(L):.0f} min={L[0]} max={L[-1]} n={len(L)}")
    print(f"280未満: {sum(1 for x in L if x < 280)}問 / 320以上: {sum(1 for x in L if x >= 320)}問")
    qo = [q for q in qs if q.get("options")]
    kl = [q["id"] for q in qo if ns["keyword_leak"](q)]
    sm = [(q["id"], ns["strawman"](q)) for q in qo if ns["strawman"](q)]
    print(f"キーワード直結: {len(kl)}問 {kl}")
    print(f"制約の裏返し: {len(sm)}問 {sm}")
    print(f"肢どうしの語の重なり: {statistics.mean([overlap(q) for q in qo]):.3f}")

main()
