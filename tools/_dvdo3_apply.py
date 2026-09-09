# -*- coding: utf-8 -*-
"""O-3是正パッチの適用（DVA-C02 / DOP-C02）。
安全装置(鉄則3): 正解肢への書き込みを検出したら1件も書かずに中断する。
保存形式: 無改変ラウンドトリップがバイト一致する形式を検出し、その形式でのみ書き戻す。
使い方: python tools/_dvdo3_apply.py DVA-C02 資料/生成/_dvdo3_patch_xx.json [--dry]
"""
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
EX = sys.argv[1]
os.environ["O3EXAM"] = EX
import _dvdo3_lib as L
L.set_exam(EX)

DRY = "--dry" in sys.argv
patch = json.load(open([a for a in sys.argv[2:] if not a.startswith("--")][0], encoding="utf-8"))

NL_LF = chr(10)
NL_CRLF = chr(13) + chr(10)


def fmt_of(raw, data):
    for indent in (1, 2, 3, 4):
        for nl in (NL_LF, NL_CRLF):
            for tr in (True, False):
                s = json.dumps(data, ensure_ascii=False, indent=indent).replace(NL_LF, nl) + (nl if tr else "")
                if s.encode("utf-8") == raw:
                    return indent, nl, tr
    return None


files = {}
for f in L.FILES:
    raw = (L.GEN / f).read_bytes()
    data = json.loads(raw.decode("utf-8"))
    fm = fmt_of(raw, data)
    if fm is None:
        raise SystemExit("中断: %s は無改変ラウンドトリップがバイト一致しません" % f)
    files[f] = [raw, data, fm]

index = {}
for f, (raw, data, fm) in files.items():
    for q in data:
        if q.get("exam") != EX:
            raise SystemExit("中断: %s に他資格の問題" % f)
        index[q["id"]] = (f, q)

errs = []
seen = set()
for p_ in patch:
    qid, let = p_["id"], p_["letter"]
    if (qid, let) in seen:
        errs.append("%s[%s]: パッチが重複" % (qid, let))
    seen.add((qid, let))
    if qid not in index:
        errs.append("%s: 未知のid" % qid)
        continue
    f, q = index[qid]
    tgt = [o for o in q["options"] if o["letter"] == let]
    if not tgt:
        errs.append("%s[%s]: 選択肢なし" % (qid, let))
        continue
    o = tgt[0]
    if o.get("correct"):
        errs.append("%s[%s]: **正解肢への書き込み**" % (qid, let))
    for k in ("text", "explanation"):
        if k in p_ and not (p_[k] or "").strip():
            errs.append("%s[%s]: %s が空" % (qid, let, k))
if errs:
    print("中断（1件も書いていません）:")
    for e in errs:
        print("  " + e)
    sys.exit(1)

touched = set()
before = {}
for p_ in patch:
    f, q = index[p_["id"]]
    before.setdefault(p_["id"], L.pairs(q)[0][0])
    o = [x for x in q["options"] if x["letter"] == p_["letter"]][0]
    if "text" in p_:
        o["text"] = p_["text"]
    if "explanation" in p_:
        o["explanation"] = p_["explanation"]
    touched.add(f)

print("%-20s %-3s %6s -> %6s" % ("id", "let", "before", "after"))
for p_ in patch:
    f, q = index[p_["id"]]
    print("%-20s %-3s %6.3f -> %6.3f" % (p_["id"], p_["letter"], before[p_["id"]], L.pairs(q)[0][0]))

if DRY:
    print()
    print("--dry のため書き込みませんでした（%d肢 / %d ファイル）" % (len(patch), len(touched)))
    sys.exit(0)

for f in sorted(touched):
    raw, data, (indent, nl, tr) = files[f]
    s = json.dumps(data, ensure_ascii=False, indent=indent).replace(NL_LF, nl) + (nl if tr else "")
    (L.GEN / f).write_bytes(s.encode("utf-8"))
    print("書込: %s (indent=%d %s trailing=%s)" % (f, indent, "CRLF" if nl == NL_CRLF else "LF", tr))
print("適用 %d肢" % len(patch))
