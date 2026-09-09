# -*- coding: utf-8 -*-
"""SAP-C02 選択肢の2文構造化パッチを適用する。

正解肢の text も書き換える作業なので sap_apply_patch.py の安全装置は使えない。
代わりに以下を強制する:
  - 正解肢を書き換えるときは "allow_correct": true を明示する
  - text は2〜3文（公式の肢は中央3文。1文はNG、4文以上は冗長なのでNG）
  - id/letter/correct は触らない（照合は _sap2s_verify.py）
  - 保存は json.dumps(ensure_ascii=False, indent=2) + 本文CRLF + 元ファイルの末尾改行
使い方: python tools/_sap2s_apply.py 資料/生成/_2s_sapN.json [--dry]
"""
import json, glob, re, statistics, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
EXAM = "SAP-C02"
def sent(t): return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
def ov(q):
    ss = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    pr = [len(ss[i] & ss[j]) / len(ss[i] | ss[j]) for i in range(len(ss)) for j in range(i+1, len(ss)) if (ss[i] | ss[j])]
    return statistics.mean(pr) if pr else 0
def cls(q):
    cor = [len(o["text"]) for o in q["options"] if o["correct"]]
    wr = [len(o["text"]) for o in q["options"] if not o["correct"]]
    if not cor or not wr: return "-"
    m = max(cor + wr)
    a, b = max(cor) == m, max(wr) == m
    return "hi" if (a and not b) else ("lo" if (b and not a) else "same")

def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    files, meta, index = {}, {}, {}
    for f in sorted(glob.glob(str(GEN / "SAP-C02_orig*.json"))):
        raw = Path(f).read_bytes()
        data = json.loads(raw.decode("utf-8"))
        files[f] = data
        meta[f] = b"\r\n" if raw.endswith(b"\r\n") else b"\n"
        # 無改変ラウンドトリップがバイト一致することを確認
        chk = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8") + meta[f]
        if chk != raw:
            print("NG: %s はラウンドトリップがバイト一致しません" % f); return 1
        for q in data:
            if q.get("exam") == EXAM: index[q["id"]] = (f, q)
    before = {qid: (ov(q), cls(q)) for qid, (_, q) in index.items()}
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
            if not t:
                errors.append("%s[%s]: text が空" % key); continue
            ns = len(sent(t))
            if ns < 2 or ns > 3:
                errors.append("%s[%s]: text が%d文（2〜3文にする）" % (qid, p["letter"], ns)); continue
            if not t.endswith(("。", "？", "！")):
                errors.append("%s[%s]: text が句点で終わっていない" % key); continue
            if o["correct"] and not p.get("allow_correct"):
                errors.append("%s[%s]: 正解肢の書き換えには allow_correct が要る" % key); continue
            if not o["correct"] and p.get("allow_correct"):
                errors.append("%s[%s]: 誤答肢に allow_correct（取り違え?）" % key); continue
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
    warn = 0
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        n2 = sum(1 for o in q["options"] if len(sent(o["text"])) >= 2)
        bo, bc = before[qid]
        ac = cls(q)
        flag = ""
        if ac != bc:
            flag = "  ★最長クラスが %s->%s に変化" % (bc, ac); warn += 1
        print("  %s 2文%d/%d 長さ[%s] 重なり %.3f->%.3f 最長%s%s"
              % (qid, n2, len(q["options"]), " ".join(str(len(o["text"])) for o in q["options"]),
                 bo, ov(q), ac, flag))
    if warn: print("  ※最長クラスが変化した問題 %d件（全体の 最長が正解 の値で最終確認する）" % warn)
    if "--dry" in sys.argv:
        print("(--dry) 書き込みませんでした"); return 0
    for f in touched:
        s = json.dumps(files[f], ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8") + meta[f]
        Path(f).write_bytes(s)
    print("OK: text %d件 / 解説 %d件 (%dファイル)" % (n_text, n_expl, len(touched)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
