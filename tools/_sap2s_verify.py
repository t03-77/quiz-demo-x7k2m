# -*- coding: utf-8 -*-
"""不変項目の照合 + 旧肢の技術トークンが残っているかの走査"""
import json, glob, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
snap = json.load(open(BASE / "tools" / "_sap2s_snapshot.json", encoding="utf-8"))
cur = {}
for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "SAP-C02_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        if q.get("exam") == "SAP-C02": cur[q["id"]] = q
bad, lost = [], []
if set(snap) != set(cur):
    bad.append("ID集合が変化: 消失%s 追加%s" % (sorted(set(snap)-set(cur))[:5], sorted(set(cur)-set(snap))[:5]))
# 技術トークン: 英数字の識別子 / サービス名 / カタカナ語 / 数値+単位
TOK = re.compile(r"[A-Za-z][A-Za-z0-9_:\-\.]{2,}|[0-9]+\s*(?:分|時間|日|か月|年|TB|GB|MB|ミリ秒|%|件|台|回|AZ)")
for qid, s in snap.items():
    q = cur.get(qid)
    if not q: continue
    for k in ("exam", "set", "domain", "level", "n_correct", "question"):
        if q.get(k) != s[k]: bad.append("%s: %s が変化" % (qid, k))
    if q.get("type", "choice") != s["type"]: bad.append("%s: type が変化" % qid)
    so, qo = s["options"], q.get("options", [])
    if len(so) != len(qo):
        bad.append("%s: 選択肢数が変化 %d->%d" % (qid, len(so), len(qo))); continue
    for a, b in zip(so, qo):
        if a["letter"] != b["letter"]: bad.append("%s: letter が変化" % qid)
        if a["correct"] != b["correct"]: bad.append("%s[%s]: correct が変化" % (qid, a["letter"]))
        if a["text"] != b["text"]:
            old = set(TOK.findall(a["text"])); new = set(TOK.findall(b["text"]))
            gone = sorted(t for t in old - new)
            if gone:
                lost.append((qid, a["letter"], "正解" if a["correct"] else "誤答", gone))
    for o in qo:
        if not (o.get("explanation") or "").strip(): bad.append("%s[%s]: 解説が空" % (qid, o["letter"]))
        if not (o.get("text") or "").strip(): bad.append("%s[%s]: text が空" % (qid, o["letter"]))
print("照合 %d問 / 不変項目の不一致 %d件" % (len(cur), len(bad)))
for b in bad[:40]: print("  " + b)
print("旧肢の技術トークンが落ちた肢: %d件" % len(lost))
for qid, L, kind, g in lost: print("  %s[%s] %s  落ちた: %s" % (qid, L, kind, ", ".join(g)))
sys.exit(1 if bad else 0)
