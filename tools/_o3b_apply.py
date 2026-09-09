# -*- coding: utf-8 -*-
"""CLF-C02 / SOA-C03 の O-3是正パッチの適用。
安全装置(鉄則3): 正解肢への書き込みを検出したら1件も書かずに中断する。
保存形式: 読み込んだバイト列を無改変で再シリアライズしてバイト一致することを
先に確認し、その形式でのみ書き戻す(形式を揃えにいかない)。
使い方: python tools/_o3b_apply.py CLF-C02 資料/生成/_o3b_clf_01.json [--dry]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _o3b_lib import GEN, files_of, pairs

exam = sys.argv[1]
DRY = "--dry" in sys.argv
patch = []
for a in sys.argv[2:]:
    if not a.startswith("--"):
        patch += json.load(open(a, encoding="utf-8"))


def fmt_of(raw, data):
    for indent in (1, 2, 3, 4):
        for nl in ("\n", "\r\n"):
            for tr in (True, False):
                s = json.dumps(data, ensure_ascii=False, indent=indent).replace("\n", nl) + (nl if tr else "")
                if s.encode("utf-8") == raw:
                    return indent, nl, tr
    return None


WRITABLE, RO = files_of(exam)
files = {}
for f in WRITABLE:
    raw = (GEN / f).read_bytes()
    data = json.loads(raw.decode("utf-8"))
    fm = fmt_of(raw, data)
    if fm is None:
        raise SystemExit("中断: %s は無改変ラウンドトリップがバイト一致しません" % f)
    files[f] = [raw, data, fm]

index = {}
for f, (raw, data, fm) in files.items():
    for q in data:
        index[q["id"]] = (f, q)

errs = []
seen = set()
for p in patch:
    qid, let = p["id"], p["letter"]
    if (qid, let) in seen:
        errs.append("%s[%s]: パッチが重複" % (qid, let))
    seen.add((qid, let))
    if qid not in index:
        errs.append("%s: 未知のid(書換対象外ファイルの可能性)" % qid)
        continue
    f, q = index[qid]
    if q.get("exam") != exam:
        errs.append("%s: 他資格(%s)" % (qid, q.get("exam")))
        continue
    tgt = [o for o in q["options"] if o["letter"] == let]
    if not tgt:
        errs.append("%s[%s]: 選択肢なし" % (qid, let))
        continue
    o = tgt[0]
    if o.get("correct"):
        errs.append("%s[%s]: **正解肢への書き込み**" % (qid, let))
    for k in ("text", "explanation"):
        if k in p and not (p[k] or "").strip():
            errs.append("%s[%s]: %s が空" % (qid, let, k))
if errs:
    print("中断(1件も書いていません):")
    for e in errs:
        print("  " + e)
    sys.exit(1)

touched = set()
before = {}
for p in patch:
    f, q = index[p["id"]]
    before.setdefault(p["id"], pairs(q)[0][0])
    o = [x for x in q["options"] if x["letter"] == p["letter"]][0]
    if "text" in p:
        o["text"] = p["text"]
    if "explanation" in p:
        o["explanation"] = p["explanation"]
    touched.add(f)

print("%-20s %-3s %6s -> %6s" % ("id", "let", "before", "after"))
for p in patch:
    f, q = index[p["id"]]
    print("%-20s %-3s %6.3f -> %6.3f" % (p["id"], p["letter"], before[p["id"]], pairs(q)[0][0]))

if DRY:
    print("\n--dry のため書き込みませんでした(%d肢 / %d ファイル)" % (len(patch), len(touched)))
    sys.exit(0)

for f in sorted(touched):
    raw, data, (indent, nl, tr) = files[f]
    s = json.dumps(data, ensure_ascii=False, indent=indent).replace("\n", nl) + (nl if tr else "")
    (GEN / f).write_bytes(s.encode("utf-8"))
    print("書込: %s (indent=%d %s trailing=%s)" % (f, indent, "CRLF" if nl == "\r\n" else "LF", tr))
print("適用 %d肢" % len(patch))
