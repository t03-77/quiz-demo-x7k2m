# -*- coding: utf-8 -*-
"""問題文の末尾を公式模試の形に揃える

公式の問題文は 98.6% が「〜はどれですか。」のような疑問で終わる。
自作は 80.7% しかなく、その大半（184件）が「（2 つ選択）」で終わっていた。

公式の複数選択問題は**選択数を問題文に書かない**。
代わりに「ステップの組み合わせはどれですか。」のように、
複数を選ぶことが文からわかる書き方をしている。

  公式: 「これらの要件を満たすステップの組み合わせはどれですか。」
  自作: 「これらの要件を満たすものはどれですか。（2 つ選択）」

選択数はアプリ側が「2つ選択」タグで示すので、問題文に書く必要はない。
（もともと書かせたのは当方の判断ミス。公式を確認せずにチェックリストへ入れた）

使い方: python tools/fix_question_end.py [--apply]
        --apply を付けないと、変更内容の確認だけ行う
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"

# 末尾の「(2 つ選択)」「（2 つ選択してください。）」「（3つ選ぶ）」など。
# 括弧の中に句点が入る形（…してください。）もあるので、閉じ括弧の直前まで許す
TAIL = re.compile(r"\s*[（(]\s*[0-9０-９一二三]\s*つ(を)?(選択|選ぶ|選ん)[^）)]*[)）]\s*[。．]?\s*$")
# 「…対応を 2 つ選択してください。」のように、末尾の一文が命令形になっている場合。
# 公式は「…ステップの組み合わせはどれですか。」と疑問形にするので、それに寄せる
TAIL_SENT = re.compile(r"([^。．]*?)(を)?\s*[0-9０-９一二三]\s*つ(を)?(選択|選ん)(して|で)?(ください|下さい)。\s*$")
QEND = re.compile(r"(か。|ですか。|でしょうか。|どれですか|どれか)\s*$")


def fix(text):
    t = (text or "").rstrip()
    before = t
    t = TAIL.sub("", t).rstrip()
    m = TAIL_SENT.search(t)
    if m and m.group(1).strip():
        # 「取るべき対応を 2 つ選択してください。」→「取るべき対応はどれですか。」
        t = t[:m.start()] + m.group(1).strip() + "はどれですか。"
    if t != before and not t.endswith(("。", "．", "？")):
        t += "。"
    return t


def main():
    apply = "--apply" in sys.argv
    changed, still_bad = [], []

    for p in sorted(GEN.glob("*_orig*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        qs = d.get("questions", d) if isinstance(d, dict) else d
        if not isinstance(qs, list):
            continue
        touched = False
        for q in qs:
            if not isinstance(q, dict) or "question" not in q:
                continue
            # マッチング・並び替えは「各サービスを1回以上選択しても構いません。」で
            # 終わるのが自然。公式も同じ形なので対象外にする
            if q.get("type") in ("matching", "ordering"):
                continue
            new = fix(q["question"])
            if new != q["question"].rstrip():
                changed.append((q.get("id"), q["question"].rstrip()[-30:], new[-30:]))
                q["question"] = new
                touched = True
            if not QEND.search(q["question"].strip()):
                still_bad.append((q.get("id"), q["question"].strip()[-34:]))
        if touched and apply:
            json.dump(qs, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("末尾を直した問題: %d件" % len(changed))
    for i, (qid, b, a) in enumerate(changed[:6]):
        print("  %s" % qid)
        print("    前: …%s" % b)
        print("    後: …%s" % a)
    print()
    print("直したあとも疑問で終わらない問題: %d件" % len(still_bad))
    per = Counter(i.split("_")[0] for i, _ in still_bad if i)
    if per:
        print("  資格別:", dict(sorted(per.items(), key=lambda x: -x[1])))
        for qid, tail in still_bad[:8]:
            print("    %-20s …%s" % (qid, tail))
    if not apply:
        print()
        print("※ 確認のみ。実際に書き込むには --apply を付けて実行する")
    return 0


if __name__ == "__main__":
    sys.exit(main())
