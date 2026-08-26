# -*- coding: utf-8 -*-
"""解説の一括書き直しで各所に残った中間ファイルを、本体JSONへ安全に取り込む。

担当ごとに出力形式が違うため、次のどちらでも受け付ける:
  A) 問題の配列 [{"id":..., "options":[{"letter":..., "explanation":...}]}, ...]
  B) 対応表 {"<問題ID>|<選択肢>": "解説"} / {"<問題ID>": {"<選択肢>": "解説"}}

安全のため explanation 以外は一切書き換えず、本体より短い解説では上書きしない
(既に書き直し済みのものを、古い中間ファイルで巻き戻さないため)。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
TMP_DIRS = ["_chunks", "_rewrite_tmp", "_tmp_patch", "_work_patches"]


def collect():
    """中間ファイルから {(問題ID, 選択肢): 解説} を集める"""
    found = {}
    for d in TMP_DIRS:
        for f in sorted((GEN / d).glob("*.json")) if (GEN / d).exists() else []:
            try:
                data = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, list):                       # 形式A
                for q in data:
                    if not isinstance(q, dict) or "id" not in q:
                        continue
                    for o in q.get("options", []):
                        ex = (o.get("explanation") or "").strip()
                        if ex:
                            key = (q["id"], o.get("letter"))
                            if len(ex) > len(found.get(key, "")):
                                found[key] = ex
            elif isinstance(data, dict):                     # 形式B
                for k, v in data.items():
                    if isinstance(v, str) and "|" in k:
                        qid, letter = k.rsplit("|", 1)
                        key = (qid.strip(), letter.strip())
                        if len(v) > len(found.get(key, "")):
                            found[key] = v
                    elif isinstance(v, dict):
                        for letter, ex in v.items():
                            if isinstance(ex, str):
                                key = (k.strip(), letter.strip())
                                if len(ex) > len(found.get(key, "")):
                                    found[key] = ex
    return found


patches = collect()
print(f"中間ファイルから収集した解説: {len(patches)}件")

applied = 0
for f in sorted(GEN.glob("*_orig*.json")):
    qs = json.load(open(f, encoding="utf-8"))
    changed = 0
    for q in qs:
        for o in q.get("options", []):
            new = patches.get((q["id"], o.get("letter")))
            # 本体より長い場合だけ採用する(巻き戻しを防ぐ)
            if new and len(new) > len(o.get("explanation") or ""):
                o["explanation"] = new
                changed += 1
    if changed:
        f.write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {f.name}: {changed}件を反映")
        applied += changed

print(f"\n反映した解説: {applied}件")
