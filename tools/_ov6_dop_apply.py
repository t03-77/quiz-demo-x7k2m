# -*- coding: utf-8 -*-
"""DOP-C02 の重なり改善パッチを適用する(既定はドライラン)。
使い方: python tools/_ov6_dop_apply.py 資料/生成/_ov6_patch_b1.json [--write]

パッチ形式: {"<id>": {"<letter>": {"text": "...", "explanation": "..."}}}
correct=true の肢を対象に含むパッチは拒否する。
"""
import json
import glob
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
BAK = GEN / "_bak_overlap4_dop_20260903"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
FIXED = ["id", "exam", "set", "type", "domain", "level", "question", "n_correct"]


def overlap(opts):
    s = [set(WORD.findall(o.get("text", ""))) for o in opts if o.get("text")]
    s = [x for x in s if x]
    ps = [len(s[i] & s[j]) / len(s[i] | s[j])
          for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] | s[j]]
    return statistics.mean(ps) if ps else 0.0


def load_files():
    out = {}
    for f in sorted(glob.glob(str(GEN / "DOP-C02_orig*.json"))):
        out[f] = json.load(open(f, encoding="utf-8"))
    return out


def save(f, data):
    s = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n")
    open(f, "wb").write(s.encode("utf-8"))


def main():
    patch = json.load(open(sys.argv[1], encoding="utf-8"))
    write = "--write" in sys.argv
    files = load_files()
    bak = {}
    for f in sorted(glob.glob(str(BAK / "DOP-C02_orig*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            bak[q["id"]] = q

    touched, errs = set(), []
    for f, qs in files.items():
        for q in qs:
            p = patch.get(q["id"])
            if not p:
                continue
            touched.add(q["id"])
            before = overlap(q["options"])
            for o in q["options"]:
                np_ = p.get(o["letter"])
                if not np_:
                    continue
                if o.get("correct"):
                    errs.append("%s %s は正解肢 -> 変更不可" % (q["id"], o["letter"]))
                    continue
                o["text"] = np_["text"]
                o["explanation"] = np_["explanation"]
            after = overlap(q["options"])
            lens = [(o["letter"], len(o["text"]), o["correct"]) for o in q["options"]]
            cmax = max(l for _, l, c in lens if c)
            amax = max(l for _, l, _ in lens)
            cl = "正解が最長" if amax == cmax else ""
            print("%s %.3f -> %.3f  [%s] %s" % (
                q["id"], before, after,
                " ".join("%s%d%s" % (a, b, "*" if c else "") for a, b, c in lens), cl))
            for o in q["options"]:
                if o["letter"] in p:
                    e = o["explanation"]
                    bad = "" if 150 <= len(e) <= 250 else "  ★解説の字数 %d" % len(e)
                    if not e.startswith("不正解です。"):
                        bad += "  ★書き出し"
                    if bad:
                        print("    %s%s" % (o["letter"], bad))
            # 不変項目
            b = bak.get(q["id"])
            if b:
                for k in FIXED:
                    if q.get(k) != b.get(k):
                        errs.append("%s %s が変わっている" % (q["id"], k))
                bo = {o["letter"]: o for o in b["options"]}
                for o in q["options"]:
                    ob = bo.get(o["letter"])
                    if ob is None:
                        errs.append("%s letter %s が増えている" % (q["id"], o["letter"]))
                        continue
                    if o["correct"] != ob["correct"]:
                        errs.append("%s %s correct が変わっている" % (q["id"], o["letter"]))
                    if o["correct"] and (o["text"] != ob["text"]
                                         or o["explanation"] != ob["explanation"]):
                        errs.append("%s %s 正解肢の内容が変わっている" % (q["id"], o["letter"]))
                if len(q["options"]) != len(b["options"]):
                    errs.append("%s 選択肢の数が変わっている" % q["id"])

    missing = set(patch) - touched
    if missing:
        errs.append("見つからない ID: %s" % ", ".join(sorted(missing)))
    if errs:
        print("\n★エラー")
        for e in errs:
            print("  " + e)
        return 1
    if write:
        for f, qs in files.items():
            if any(q["id"] in patch for q in qs):
                save(f, qs)
                print("saved: " + f)
    else:
        print("\n(ドライラン。--write で保存)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
