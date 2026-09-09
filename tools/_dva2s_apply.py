# -*- coding: utf-8 -*-
"""DVA-C02 選択肢の2文構造化パッチを適用する。

正解肢の text も書き換える作業なので dva_apply_patch.py の安全装置は使えない。
代わりに次を強制する:
  - 正解肢を書き換えるときは "allow_correct": true を明示する（誤答肢に付いていたら中断）
  - text は必ず2文以上
  - id / letter / correct は触らない（照合は _dva2s_verify.py）
  - 保存形式は元ファイルごとに検出（改行コード・インデント・末尾改行）し、
    無改変ラウンドトリップがバイト一致することを毎回確認してから書く
使い方: python tools/_dva2s_apply.py 資料/生成/_dva2s_patch.json [--dry]
"""
import json, glob, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAM = "DVA-C02"


def sent(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]


WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def ov(q):
    import statistics
    ss = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    pr = [len(ss[i] & ss[j]) / len(ss[i] | ss[j])
          for i in range(len(ss)) for j in range(i + 1, len(ss)) if (ss[i] | ss[j])]
    return statistics.mean(pr) if pr else 0


def detect(raw):
    txt = raw.decode("utf-8")
    nl = "\r\n" if b"\r\n" in raw else "\n"
    lines = txt.replace("\r\n", "\n").split("\n")
    ind = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 2
    tail = nl if txt.endswith("\n") else ""
    return nl, ind or 2, tail


def render(data, fmt):
    nl, ind, tail = fmt
    return (json.dumps(data, ensure_ascii=False, indent=ind).replace("\n", nl) + tail).encode("utf-8")


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, meta, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / (EXAM + "_orig*.json")))):
        raw = Path(f).read_bytes()
        data = json.loads(raw.decode("utf-8"))
        fmt = detect(raw)
        if render(data, fmt) != raw:
            print("NG: %s の無改変ラウンドトリップがバイト一致しません。何も書き込みません" % Path(f).name)
            return 1
        files[f], meta[f] = data, fmt
        for q in data:
            if q.get("exam") == EXAM:
                index[q["id"]] = (f, q)
    before_ov = {qid: ov(q) for qid, (_, q) in index.items()}
    errors, touched, seen = [], set(), set()
    n_text = n_expl = n_cor = n_wrong = 0
    for p in patches:
        qid, L = p["id"], p["letter"]
        if qid not in index:
            errors.append("%s: 該当なし" % qid)
            continue
        f, q = index[qid]
        opts = [o for o in q["options"] if o["letter"] == L]
        if not opts:
            errors.append("%s[%s]: 選択肢なし" % (qid, L))
            continue
        o = opts[0]
        if (qid, L) in seen:
            errors.append("%s[%s]: 重複パッチ" % (qid, L))
            continue
        seen.add((qid, L))
        if "text" in p:
            t = p["text"].strip()
            if len(sent(t)) < 2:
                errors.append("%s[%s]: text が2文未満" % (qid, L))
                continue
            if o["correct"] and not p.get("allow_correct"):
                errors.append("%s[%s]: 正解肢の書き換えには allow_correct が要る" % (qid, L))
                continue
            if not o["correct"] and p.get("allow_correct"):
                errors.append("%s[%s]: 誤答肢に allow_correct が付いている(取り違え?)" % (qid, L))
                continue
            if len(sent(o["text"])) >= 2:
                errors.append("%s[%s]: 既に2文以上（対象外のはず）" % (qid, L))
                continue
            if t != o["text"]:
                o["text"] = t
                n_text += 1
                n_cor += bool(o["correct"])
                n_wrong += (not o["correct"])
                touched.add(f)
        if "expl" in p:
            e = p["expl"].strip()
            head = "正解です" if o["correct"] else "不正解です"
            if not e.startswith(head):
                errors.append("%s[%s]: 解説は「%s」で始める" % (qid, L, head))
                continue
            if e != o.get("explanation"):
                o["explanation"] = e
                n_expl += 1
                touched.add(f)
    if errors:
        print("NG: %d件のため何も書き込みませんでした" % len(errors))
        for e in errors:
            print("  " + e)
        return 1
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wr = [o for o in q["options"] if not o["correct"]]
        mx = max(len(o["text"]) for o in q["options"])
        cls = "hi" if (max(len(o["text"]) for o in cor) == mx and max(len(o["text"]) for o in wr) != mx) else \
              ("lo" if (max(len(o["text"]) for o in wr) == mx and max(len(o["text"]) for o in cor) != mx) else "same")
        n2 = sum(1 for o in q["options"] if len(sent(o["text"])) >= 2)
        print("  %s 2文%d/%d [%s] %-4s 重なり%.3f->%.3f" % (
            qid, n2, len(q["options"]), " ".join(str(len(o["text"])) for o in q["options"]),
            cls, before_ov[qid], ov(q)))
    if "--dry" in sys.argv:
        print("(--dry) text %d件(正解 %d / 誤答 %d) 解説 %d件" % (n_text, n_cor, n_wrong, n_expl))
        return 0
    for f in touched:
        Path(f).write_bytes(render(files[f], meta[f]))
    print("OK: text %d件(正解 %d / 誤答 %d) 解説 %d件 (%dファイル)" % (n_text, n_cor, n_wrong, n_expl, len(touched)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
