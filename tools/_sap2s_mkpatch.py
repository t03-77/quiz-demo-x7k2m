# -*- coding: utf-8 -*-
"""分割方式のパッチを作る（全肢を加筆なしで割れる問題だけを対象にする）"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sap2s_split import main as scan
BASE = Path(__file__).resolve().parent.parent
ok_q, part_q, no_q = scan()
patch = []
for q, good in ok_q:
    for o in q["options"]:
        if o["letter"] in good:
            p = {"id": q["id"], "letter": o["letter"], "text": good[o["letter"]]}
            if o["correct"]:
                p["allow_correct"] = True
            patch.append(p)
out = BASE / "資料" / "生成" / "_2s_sap" / "patch_split.json"
out.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print()
print("patch: %d肢 / %d問 -> %s" % (len(patch), len(ok_q), out.name))
