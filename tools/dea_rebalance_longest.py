# -*- coding: utf-8 -*-
"""DEA-C01 の「正解が最長」の割合を公式模試の水準に近づける。

誤答肢を長くした結果、今度は「一番長い選択肢は誤答」という逆の当て方が
成立してしまう。公式模試では 40% 程度の問題で正解肢が最長になっており、
その水準にそろえるため、指定した問題数だけ最長の誤答肢の末尾の一文を外して
正解肢が最長に戻るようにする。

外すのは長さ調整のために足した補足の一文だけで、解説がその内容に触れている
場合は対象にしない(解説と選択肢が食い違わないようにするため)。
"""
import json
import glob
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
TARGET_PCT = 30


def load():
    files, index = {}, {}
    indents = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if q.get("exam") == "DEA-C01" and q.get("set") == "orig" and q.get("type", "choice") == "choice":
                index[q["id"]] = (f, q)
    return files, indents, index


def keywords(s):
    return set(re.findall(r"[A-Za-z][A-Za-z0-9]{2,}|[ぁ-んァ-ヶ一-龠]{3,}", s))


def main():
    files, indents, index = load()
    ids = sorted(index)
    need = round(len(ids) * TARGET_PCT / 100)
    done = 0
    touched = set()
    for qid in ids:
        if done >= need:
            break
        f, q = index[qid]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        cmax = max(len(o["text"]) for o in cor)
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        top = max(wrong, key=lambda o: len(o["text"]))
        if len(top["text"]) <= cmax:
            continue  # すでに正解肢が最長
        sents = [s for s in re.split(r"(?<=。)", top["text"]) if s]
        if len(sents) < 2:
            continue
        trimmed = "".join(sents[:-1])
        # 末尾の一文を外しても他の誤答肢が正解肢を超えるなら意味がない
        others = [len(o["text"]) for o in wrong if o is not top]
        if others and max(others) > cmax:
            continue
        if not (len(trimmed) >= 0.8 * cmean and len(trimmed) < cmax):
            continue
        # 解説がその一文の内容に触れているなら外さない
        expl = top.get("explanation") or ""
        if keywords(sents[-1]) & keywords(expl):
            continue
        top["text"] = trimmed
        touched.add(f)
        done += 1
        print(f"  {qid}[{top['letter']}] 末尾の一文を削除 -> {len(trimmed)}字 (正解 {cmax}字)")

    for f in touched:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1),
                           encoding="utf-8")
    print(f"{done}問で正解肢を最長に戻しました (目標 {need}問)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
