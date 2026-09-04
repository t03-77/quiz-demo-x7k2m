# -*- coding: utf-8 -*-
"""AIP-C01 の question だけを差し替える(長さ調整)。
使い方: python tools/_aiplen_apply.py 資料/生成/_aiplen_p01.json
パッチ形式: [{"id":"...","before":"旧question先頭40字","question":"新しい全文"}]
question 以外は一切触らない。書式(CRLF/indent2/末尾改行)は元ファイルどおり保つ。
"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"

def serialize(data, had_trailing_nl):
    s = json.dumps(data, ensure_ascii=False, indent=2)
    s = s.replace("\n", "\r\n")
    if had_trailing_nl:
        s += "\r\n"
    return s.encode("utf-8")

def main(patch_path, dry=False):
    patches = {p["id"]: p for p in json.load(open(patch_path, encoding="utf-8"))}
    done = set()
    for f in sorted(glob.glob(str(GEN / "AIP-C01_orig*.json"))):
        raw = Path(f).read_bytes()
        text = raw.decode("utf-8")
        had_nl = text.endswith("\r\n")
        data = json.loads(text)
        # 書き戻しが元と同一になることを先に確認する
        if serialize(data, had_nl) != raw:
            raise SystemExit(f"{f}: 書式再現に失敗。中断")
        changed = False
        for q in data:
            p = patches.get(q.get("id"))
            if not p:
                continue
            if not q["question"].startswith(p["before"]):
                raise SystemExit(f"{q['id']}: before 不一致。中断")
            q["question"] = p["question"]
            done.add(q["id"])
            changed = True
        if changed and not dry:
            Path(f).write_bytes(serialize(data, had_nl))
            print(f"更新 {Path(f).name}")
    miss = set(patches) - done
    if miss:
        raise SystemExit(f"未適用: {sorted(miss)}")
    print(f"{len(done)}問に適用" + ("(ドライラン)" if dry else ""))

main(sys.argv[1], "--dry" in sys.argv)
