# -*- coding: utf-8 -*-
"""SOA-C03 の誤答肢書き直しパッチを適用する。

「一番長い選択肢を選べば当たる」状態を解消するため、誤答肢を正解肢と
同程度の長さ・具体性に書き直す。正解肢と、id/question などの不変項目は
触らない。パッチは誤答肢だけを対象とし、対象外を書き換えようとしたら
適用せず中断する(過去に別内容で上書きして問題が消えかけた事故があるため)。

パッチ1件の形式:
  {"id": "...", "letter": "B",
   "text": "新しい誤答肢テキスト",
   # 解説は次のいずれかで更新(省略時は据え置き)
   "expl": "差し替える解説全文",
   "ins_after": "既存解説内のアンカー", "ins": "その直後に差し込む文",
   "sub": ["置換前の部分文字列", "置換後"]}

使い方: python tools/soa_apply_patch.py 資料/生成/_soa_patch_01.json
"""
import json
import glob
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def main(patch_path):
    patches = json.load(open(patch_path, encoding="utf-8"))
    # id -> (ファイル, 問題) を作る
    files = {}
    indents = {}
    index = {}
    for f in sorted(glob.glob(str(GEN / "*_orig*.json"))):
        raw = Path(f).read_text(encoding="utf-8")
        data = json.loads(raw)
        files[f] = data
        # 既存のインデント幅を保って書き戻す(無関係な差分を出さないため)
        lines = raw.split("\n")
        indents[f] = (len(lines[1]) - len(lines[1].lstrip())) if len(lines) > 1 else 1
        for q in data:
            if q.get("exam") == "SOA-C03":
                index[q["id"]] = (f, q)

    errors = []
    touched_files = set()
    n_text = n_expl = 0
    seen = set()
    for p in patches:
        key = (p["id"], p["letter"])
        if key in seen:
            errors.append(f"{key}: 同じ選択肢へのパッチが重複")
            continue
        seen.add(key)
        if p["id"] not in index:
            errors.append(f"{p['id']}: 該当問題なし")
            continue
        f, q = index[p["id"]]
        opts = [o for o in q["options"] if o["letter"] == p["letter"]]
        if not opts:
            errors.append(f"{p['id']}[{p['letter']}]: 該当選択肢なし")
            continue
        o = opts[0]
        if o["correct"]:
            errors.append(f"{p['id']}[{p['letter']}]: 正解肢は書き換え禁止")
            continue
        if "text" in p:
            if not p["text"].strip():
                errors.append(f"{p['id']}[{p['letter']}]: text が空")
                continue
            if p["text"] != o["text"]:
                o["text"] = p["text"]
                n_text += 1
                touched_files.add(f)
        ex = o.get("explanation") or ""
        new_ex = None
        if "expl" in p:
            new_ex = p["expl"]
        elif "ins_after" in p:
            anchor = p["ins_after"]
            if ex.count(anchor) != 1:
                errors.append(f"{p['id']}[{p['letter']}]: アンカーが{ex.count(anchor)}箇所 -> {anchor[:24]}")
                continue
            i = ex.index(anchor) + len(anchor)
            new_ex = ex[:i] + p["ins"] + ex[i:]
        elif "append" in p:
            # 誤答肢に新しい要素を足したときに、その要素への評価を解説の末尾に補う
            if p["append"] in ex:
                errors.append(f"{p['id']}[{p['letter']}]: 追記内容が既に解説にある")
                continue
            new_ex = ex.rstrip() + p["append"]
        elif "sub" in p:
            old, new = p["sub"]
            if ex.count(old) != 1:
                errors.append(f"{p['id']}[{p['letter']}]: 置換対象が{ex.count(old)}箇所 -> {old[:24]}")
                continue
            new_ex = ex.replace(old, new)
        if new_ex is not None and new_ex != ex:
            if not new_ex.lstrip().startswith("不正解"):
                errors.append(f"{p['id']}[{p['letter']}]: 誤答の解説は「不正解です。」で始める必要がある")
                continue
            o["explanation"] = new_ex
            n_expl += 1
            touched_files.add(f)

    if errors:
        print(f"NG: {len(errors)}件のため何も書き込みませんでした")
        for e in errors:
            print("  " + e)
        return 1

    # 長さのそろい具合を、パッチ対象の問題について報告する
    for qid in sorted({p["id"] for p in patches}):
        q = index[qid][1]
        cor = [o for o in q["options"] if o["correct"]]
        wrong = [o for o in q["options"] if not o["correct"]]
        cmax = max(len(o["text"]) for o in cor)
        cmean = sum(len(o["text"]) for o in cor) / len(cor)
        wmean = sum(len(o["text"]) for o in wrong) / len(wrong)
        ng = [f"{o['letter']}:{len(o['text'])}" for o in wrong
              if not (0.8 * cmean <= len(o["text"]) <= 1.2 * cmean)]
        flag = []
        if max(len(o["text"]) for o in wrong) <= cmax:
            flag.append("正解が最長")
        if ng:
            flag.append("範囲外 " + ",".join(ng))
        print(f"  {qid} 正解{cmean:.0f} 誤答平均{wmean:.0f} 比{cmean/wmean:.2f} "
              f"[{' '.join(str(len(o['text'])) for o in q['options'])}] {' / '.join(flag)}")

    if "--dry" in sys.argv:
        print("(--dry のため書き込みませんでした)")
        return 0

    for f in touched_files:
        Path(f).write_text(json.dumps(files[f], ensure_ascii=False, indent=indents[f] or 1), encoding="utf-8")
    print(f"OK: 誤答肢テキスト {n_text}件 / 解説 {n_expl}件 を更新 ({len(touched_files)}ファイル)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
