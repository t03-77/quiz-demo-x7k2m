# -*- coding: utf-8 -*-
"""飾りと判定した追加文を question から取り除く。"""
import json, glob, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
# どの誤答も落とさないため撤去する断片
DROP = {
  "AIP-C01_orig_309": ["、プロンプトと応答の本文まで"],
  "AIP-C01_orig_317": ["監査人は、本文の記録に加えて、誰がいつどの API を呼び出したかの記録も求めています。"],
}
idx = {}
for f in sorted(glob.glob(str(GEN / "AIP-C01_orig*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        idx[q["id"]] = q
out = []
for qid, frags in DROP.items():
    q = idx[qid]["question"]
    n = q
    for fr in frags:
        if n.count(fr) != 1:
            raise SystemExit(f"{qid}: 断片が{n.count(fr)}回 -> {fr[:20]}")
        n = n.replace(fr, "")
    print(f"{qid}  {len(q)} -> {len(n)}")
    out.append({"id": qid, "before": q[:12], "question": n})
Path("資料/生成/_aiplen_p10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
