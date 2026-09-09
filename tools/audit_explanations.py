# -*- coding: utf-8 -*-
"""解説の分量を公式模試の水準と比較する。

解説が短いと「なぜ間違えたのか」が分からず、復習しても伸びない。
公式模試の解説(選択肢あたり平均250〜550字)を基準に、資格ごとの達成度を出す。
"""
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# 公式解説は「〜を参照してください。https://...」という誘導が本文の半分近くを占める。
# 説明の中身どうしを比べるため、URLと誘導文を落としてから字数を測る。
URL = re.compile(r"https?://\S+")
POINTER = re.compile(r"[^。\n]*(参照してください|に関するページ)[^。\n]*。?")


def clean(s):
    s = URL.sub("", s or "")
    s = POINTER.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def official_baseline():
    d = json.load(open(BASE / "資料" / "変換済み" / "questions_all.json", encoding="utf-8"))
    out = defaultdict(list)
    for q in d["questions"]:
        if q["set"] not in ("exam", "pretest") or q["type"] != "choice":
            continue
        for o in q["options"]:
            out[q["exam"]].append(len(clean(o.get("explanation", ""))))
    return out


def generated():
    out = defaultdict(list)
    for f in sorted((BASE / "資料" / "生成").glob("*_orig*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            for o in q.get("options", []):
                out[q["exam"]].append(len(clean(o.get("explanation", ""))))
    return out


ref, gen = official_baseline(), generated()
print(f"{'資格':<9}{'公式平均':>8}{'生成平均':>8}{'達成率':>8}   判定")
rows = []
for exam in sorted(gen):
    g = int(st.mean(gen[exam]))
    r = int(st.mean(ref[exam])) if ref.get(exam) else 0
    pct = (g / r * 100) if r else 0
    mark = "★ 到達" if pct >= 85 else ("△ もう少し" if pct >= 60 else "✗ 不足")
    rows.append((pct, exam, r, g, mark))
    print(f"{exam:<9}{r:>8}{g:>8}{pct:>7.0f}%   {mark}")
done = sum(1 for p, *_ in rows if p >= 85)
print(f"\n公式水準(85%以上)に到達: {done}/{len(rows)}資格")

# ここが見ているのは 資料/生成/*_orig*.json の options[].explanation だけ。
# AIP-C01 の一問一答221問は生成元が外部(06_lessons/genai_dev_pro/quiz/questions.json)で、
# 肢ごとの解説を持たず全体解説だけを持つ形なので、上の集計には1問も入っていない。
# 2026-09-09 に全体解説を中央51→130字へ充実させたとき、この表は1ポイントも動かず、
# 「測れていない」ことに気づくまで成果が見えなかった。測っていない範囲は明示する。
FLASH = BASE.parent.parent / "06_lessons" / "genai_dev_pro" / "quiz" / "questions.json"
if FLASH.exists():
    try:
        _d = json.load(open(FLASH, encoding="utf-8"))
        _qs = _d if isinstance(_d, list) else _d.get("questions", [])
        _lens = sorted(len(clean(q.get("explanation", ""))) for q in _qs)
        if _lens:
            print("\n※上の表に含まれない: AIP-C01 の一問一答 %d問"
                  "（全体解説のみ・中央 %d字 / 最短 %d字）。"
                  "公式模試に一問一答形式が無いため達成率は出せない"
                  % (len(_lens), _lens[len(_lens) // 2], _lens[0]))
    except Exception as _e:
        print("\n※一問一答の集計をスキップ: %s" % _e)
else:
    print("\n※AIP-C01 の一問一答は上の表に含まれない（生成元が見つからず字数も出せない）")
