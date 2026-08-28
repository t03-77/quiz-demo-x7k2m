# -*- coding: utf-8 -*-
"""MLA-C01 の書き直しが「触ってはいけない項目」を壊していないか検査する。

mla_snapshot.py が保存した着手前の状態と現在のファイルを突き合わせ、
id / question / n_correct / letter / correct / 正解肢 text の一致を確認する。
あわせて、誤答肢の長さが正解肢に対してどの程度そろったかも出す。
"""
import json
import glob
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SNAP = BASE / "tools" / "_mla_snapshot.json"


def current():
    cur = {}
    for f in sorted(glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            if q.get("exam") == "MLA-C01":
                cur[q["id"]] = q
    return cur


def main():
    snap = json.load(open(SNAP, encoding="utf-8"))
    cur = current()
    bad = []
    if set(snap) != set(cur):
        bad.append(f"問題IDの集合が変化: 消失 {sorted(set(snap)-set(cur))[:5]} / 追加 {sorted(set(cur)-set(snap))[:5]}")
    for qid, s in snap.items():
        q = cur.get(qid)
        if not q:
            continue
        for key in ("exam", "set", "type", "domain", "level", "question", "n_correct"):
            if key == "type":
                if q.get("type", "choice") != s["type"]:
                    bad.append(f"{qid}: type が変化")
                continue
            if q.get(key) != s[key]:
                bad.append(f"{qid}: {key} が変化")
        so, qo = s["options"], q.get("options", [])
        if len(so) != len(qo):
            bad.append(f"{qid}: 選択肢の数が変化 {len(so)} -> {len(qo)}")
            continue
        for a, b in zip(so, qo):
            if a["letter"] != b["letter"]:
                bad.append(f"{qid}: letter が変化 {a['letter']} -> {b['letter']}")
            if a["correct"] != b["correct"]:
                bad.append(f"{qid}[{a['letter']}]: correct が変化")
            if a["correct"] and a["text"] != b["text"]:
                bad.append(f"{qid}[{a['letter']}]: 正解肢の text が変化")
        for o in qo:
            if not (o.get("explanation") or "").strip():
                bad.append(f"{qid}[{o['letter']}]: 解説が空")

    # 長さのそろい具合
    ratios, out_of_band, longest = [], 0, 0
    nopt = 0
    for qid, q in cur.items():
        if q.get("type", "choice") != "choice":
            continue
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        if not cor or not wrong:
            continue
        clen = statistics.mean(len(o["text"]) for o in cor)
        ratios.append(clen / statistics.mean(len(o["text"]) for o in wrong))
        lens = [len(o["text"]) for o in q["options"]]
        if max(lens) == max(len(o["text"]) for o in cor):
            longest += 1
        for o in wrong:
            nopt += 1
            if not (0.8 * clen <= len(o["text"]) <= 1.2 * clen):
                out_of_band += 1

    n = len(ratios)
    print(f"検査した問題: {len(cur)}問 (choice {n}問)")
    print(f"不変項目の不一致: {len(bad)}件")
    for b in bad[:30]:
        print("  " + b)
    if len(bad) > 30:
        print(f"  …ほか{len(bad)-30}件")
    print(f"正解が最長: {100*longest//n}%  正解/誤答の長さ比(中央値): {statistics.median(ratios):.2f}")
    print(f"誤答肢のうち 0.8〜1.2倍の範囲外: {out_of_band}/{nopt}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
