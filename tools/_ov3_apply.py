# -*- coding: utf-8 -*-
"""SCS-C03 誤答肢の組み直しパッチを適用する(ファイルの改行/インデント形式を保存)。

パッチ1件: {"id":"...","letter":"B","text":"...","expl":"不正解です。..."}
正解肢・不変項目には一切触らない(触ろうとしたら1件も書かずに中断)。
使い方: python tools/_ov3_apply.py <patch.json> [--dry]
"""
import json, glob, sys, re, statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAM = "SCS-C03"
IMMUT = ("id", "exam", "set", "type", "domain", "level", "n_correct", "question")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def snap(q):
    return json.dumps({k: q.get(k) for k in IMMUT}, ensure_ascii=False, sort_keys=True) + "|" + \
        json.dumps([[o.get("letter"), bool(o.get("correct")),
                     o["text"] if o.get("correct") else None,
                     o.get("explanation") if o.get("correct") else None]
                    for o in q.get("options") or []], ensure_ascii=False)


def ovl(q):
    s = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    s = [x for x in s if x]
    ps = [len(s[i] & s[j]) / len(s[i] | s[j]) for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else 0


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, meta, index, before = {}, {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "SCS-C03_orig*.json"))):
        raw = Path(f).read_bytes().decode("utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        l1 = lines[1].rstrip(chr(13)) if len(lines) > 1 else ""
        indent = len(l1) - len(l1.lstrip())
        meta[f] = dict(indent=indent or 2,
                       crlf="\r\n" in raw,
                       tail=raw.endswith("\n"))
        for q in data:
            if q.get("exam") == EXAM:
                index[q["id"]] = (f, q)
                before[q["id"]] = snap(q)

    errors, touched, seen = [], set(), set()
    n_text = n_expl = 0
    for p in patches:
        qid, L = p["id"], p["letter"]
        if (qid, L) in seen:
            errors.append(f"{qid}[{L}]: パッチ重複"); continue
        seen.add((qid, L))
        if qid not in index:
            errors.append(f"{qid}: 該当問題なし"); continue
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] == L]
        if not opts:
            errors.append(f"{qid}[{L}]: 該当選択肢なし"); continue
        o = opts[0]
        if o.get("correct"):
            errors.append(f"{qid}[{L}]: 正解肢は書き換え禁止"); continue
        if "text" in p:
            t = p["text"].strip()
            if not t:
                errors.append(f"{qid}[{L}]: text が空"); continue
            if t != o["text"]:
                o["text"] = t; n_text += 1; touched.add(f)
        if "expl" in p:
            e = p["expl"].strip()
            if not e.startswith("不正解です。"):
                errors.append(f"{qid}[{L}]: 解説は「不正解です。」で始める"); continue
            if not (140 <= len(e) <= 265):
                errors.append(f"{qid}[{L}]: 解説 {len(e)}字 (150〜250字目安)"); continue
            if e != o.get("explanation"):
                o["explanation"] = e; n_expl += 1; touched.add(f)

    for qid in sorted({p["id"] for p in patches}):
        if qid in index and snap(index[qid][1]) != before[qid]:
            errors.append(f"{qid}: 不変項目/正解肢が変化した")

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors: print("  " + e)
        return 1

    longest = 0
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        ng = [f"{o['letter']}:{len(o['text'])}" for o in wrong if not (0.9 * cmean <= len(o["text"]) <= 1.1 * cmean)]
        flag = []
        if max(len(o["text"]) for o in wrong) < max(len(o["text"]) for o in cor):
            flag.append("正解が最長"); longest += 1
        if ng: flag.append("±10%外 " + ",".join(ng))
        print(f"  {qid} ov={ovl(q):.3f} 正解{cmean:.0f} [{' '.join(str(len(o['text'])) for o in q['options'])}] {' / '.join(flag)}")
    print(f"-- 正解が最長: {longest}/{len({p['id'] for p in patches})}問")

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)"); return 0
    for f in touched:
        m = meta[f]
        s = json.dumps(files[f], ensure_ascii=False, indent=m["indent"])
        if m["tail"]: s += "\n"
        if m["crlf"]: s = s.replace("\n", "\r\n")
        Path(f).write_bytes(s.encode("utf-8"))
    print(f"OK: 誤答肢 {n_text}件 / 解説 {n_expl}件 ({len(touched)}ファイル)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
