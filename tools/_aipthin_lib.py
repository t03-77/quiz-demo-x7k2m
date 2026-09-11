# -*- coding: utf-8 -*-
"""AIP-C01「重なりが薄い問題」作業用の共通関数（audit_pattern.py と同じ定義）"""
import json, re, statistics
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")

def load():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig" and q.get("options")]

def ov(q, texts=None):
    """1問の肢どうしの語の重なり（audit_pattern.overlap_stats と同一）"""
    ops = q["options"]
    ts = texts if texts is not None else [o.get("text", "") for o in ops]
    sets = [set(WORD.findall(t)) for t in ts if t]
    sets = [s for s in sets if s]
    if len(sets) < 2:
        return None
    pairs = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            u = sets[i] | sets[j]
            if u:
                pairs.append(len(sets[i] & sets[j]) / len(u))
    return statistics.mean(pairs) if pairs else None
