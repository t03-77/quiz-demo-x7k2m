# -*- coding: utf-8 -*-
"""SCS-C03 選択肢の2文構造化パッチを適用する。

正解肢の text も書き換える作業なので、scs_apply_patch.py の安全装置は使えない。
代わりに以下を強制する:
  - 正解肢を書き換えるときは "allow_correct": true を明示する
  - text は必ず2文以上（(?<=[。？！]) で分割して2要素以上）
  - id/letter/correct は触らない（照合は _scs2s_verify.py）
  - 改行コードとインデントは既存ファイルに合わせる
使い方: python tools/_scs2s_apply.py 資料/生成/_2s_batchN.json [--dry]
"""
import json, glob, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAM = "SCS-C03"
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def ov(q):
    import statistics
    ss = [set(WORD.findall(o.get("text",""))) for o in q["options"] if o.get("text")]
    pr = [len(ss[i]&ss[j])/len(ss[i]|ss[j]) for i in range(len(ss)) for j in range(i+1,len(ss)) if (ss[i]|ss[j])]
    return statistics.mean(pr) if pr else 0

def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, meta, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "SCS-C03_orig*.json"))):
        raw = Path(f).read_bytes()
        txt = raw.decode("utf-8")
        data = json.loads(txt)
        files[f] = data
        nl = "\r\n" if b"\r\n" in raw else "\n"
        lines = txt.replace("\r\n", "\n").split("\n")
        indent = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 2
        meta[f] = (nl, indent or 2)
        for q in data:
            if q.get("exam") == EXAM: index[q["id"]] = (f, q)
    before_ov = {q["id"]: ov(q) for _, q in index.values()}
    errors, touched, seen = [], set(), set()
    n_text = n_expl = 0
    for p in patches:
        qid = p["id"]
        if qid not in index:
            errors.append("%s: 該当なし" % qid); continue
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] == p["letter"]]
        if not opts:
            errors.append("%s[%s]: 選択肢なし" % (qid, p["letter"])); continue
        o = opts[0]
        key = (qid, p["letter"])
        if key in seen:
            errors.append("%s: 重複パッチ" % str(key)); continue
        seen.add(key)
        if "text" in p:
            t = p["text"].strip()
            if not t: errors.append("%s[%s]: text が空" % key); continue
            if len(sent(t)) < 2:
                errors.append("%s[%s]: text が2文未満" % key); continue
            if o["correct"] and not p.get("allow_correct"):
                errors.append("%s[%s]: 正解肢の書き換えには allow_correct が要る" % key); continue
            if not o["correct"] and p.get("allow_correct"):
                errors.append("%s[%s]: 誤答肢に allow_correct が付いている(取り違え?)" % key); continue
            if t != o["text"]:
                o["text"] = t; n_text += 1; touched.add(f)
        if "expl" in p:
            e = p["expl"].strip()
            head = "正解です" if o["correct"] else "不正解です"
            if not e.startswith(head):
                errors.append("%s[%s]: 解説は「%s。」で始める" % (qid, p["letter"], head)); continue
            if e != o.get("explanation"):
                o["explanation"] = e; n_expl += 1; touched.add(f)
    if errors:
        print("NG: %d件のため何も書き込みませんでした" % len(errors))
        for e in errors: print("  " + str(e))
        return 1
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wr = [o for o in q["options"] if not o["correct"]]
        cmean = sum(len(o["text"]) for o in cor)/len(cor)
        mx = max(len(o["text"]) for o in q["options"])
        cls = "hi" if (max(len(o["text"]) for o in cor) == mx and max(len(o["text"]) for o in wr) != mx) else \
              ("lo" if (max(len(o["text"]) for o in wr) == mx and max(len(o["text"]) for o in cor) != mx) else "same")
        ng = [o["letter"] for o in wr if not (0.8*cmean <= len(o["text"]) <= 1.2*cmean)]
        n2 = sum(1 for o in q["options"] if len(sent(o["text"])) >= 2)
        print("  %s 2文%d/%d 正解平均%.0f [%s] %s 重なり%.3f->%.3f %s" % (qid, n2, len(q["options"]), cmean,
              " ".join(str(len(o["text"])) for o in q["options"]), cls,
              before_ov[qid], ov(q), ("範囲外 " + ",".join(ng)) if ng else ""))
    if "--dry" in sys.argv:
        print("(--dry)"); return 0
    for f in touched:
        nl, ind = meta[f]
        s = json.dumps(files[f], ensure_ascii=False, indent=ind) + "\n"
        Path(f).write_bytes(s.replace("\n", nl).encode("utf-8"))
    print("OK: text %d件 / 解説 %d件 (%dファイル)" % (n_text, n_expl, len(touched)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
