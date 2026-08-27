# -*- coding: utf-8 -*-
"""「問題文を読むだけで切れる誤答」を数える

出典を伏せた判定で、消去法が成立する原因の最多がこれだった（60問中30問以上）。

  問題文「運用上のオーバーヘッドを最小限に抑えながら…」
  誤答  「担当者が毎日コンソールを確認して…」

AWSの知識がなくても切れる。公式にはこの型がほとんどない。
さらに公式では「自分でLambdaを書く」「手動で対応する」が**正解になることが11.8%ある**ため、
「手動と書いてあれば誤答」というメタ規則自体が成立しない。

もう一つ数えるのが「キーワード直結」。
  問題文「アクセス頻度が予測できない」→ 正解「S3 Intelligent-Tiering」
問題文の語が正解肢にだけ出ていると、文字列を照合するだけで当たる。

使い方: python tools/audit_strawman.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"

# 問題文が「手間をかけたくない」と言っているサイン。
# 判定者が挙げた実例に合わせて広めに取る（当初は狭すぎて、公式0問という不自然な結果になった）
LOW_EFFORT = re.compile(
    r"(運用(上の)?(負荷|オーバーヘッド|コスト)|オペレーション(上の)?(負荷|効率|オーバーヘッド)"
    r"|管理の手間|最小限の(労力|運用|管理|開発)|最も(少ない|小さい)(労力|運用|開発)"
    r"|運用を自動化|人手を(かけ|介さ)|手作業を(避け|なくし|減らし)|自動的に"
    r"|追加の(開発|実装|コード)を(避け|せず|不要)|コード(を|の)変更(せず|しない|なし|を最小)"
    r"|既存の(アプリケーション|コード)(を|は)変更(せず|しない)"
    r"|マネージド(サービス|型)|サーバーレス|保守を(避け|不要)|新たに(開発|構築)(せず|しない))")

# 誤答が「人手でやる」「自前で作る」と自白しているサイン。
# 注意: これらが**正解になる**問題も公式には存在する（自前Lambdaが正解など）。
# 「この語があれば誤答」というメタ規則を作らないため、正解側の出現数も併せて数えている。
BY_HAND = re.compile(
    r"(担当者が|管理者が(手動|定期的)|運用担当者|従業員が|エンジニアが(手動|毎)"
    r"|手動で(実行|確認|更新|対応|設定|適用|集約|作成|追加|削除|同期|コピー)"
    r"|手作業で|目視で|コンソールを(定期的に|毎日|毎週|1時間ごとに|都度)?(確認|操作)"
    r"|表計算|スプレッドシート|台帳|Wiki に(記録|文書化)|口頭で|メールで(通知して)?対応"
    r"|自前で(実装|構築|開発)|独自に(実装|開発)|カスタムスクリプト|スクリプトを(自作|作成して定期)"
    r"|アプリケーション(のコード)?を(修正|改修|書き換え)"
    r"|各アカウントで(個別に|それぞれ)|1つずつ|1台ずつ)")


def load():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig" and q.get("options")]


def strawman(q):
    """問題文の「手間をかけたくない」に、誤答が真っ向から反しているか"""
    if not LOW_EFFORT.search(q.get("question", "")):
        return []
    return [o.get("letter") for o in q["options"]
            if not o.get("correct") and BY_HAND.search(o.get("text", ""))]


def by_hand_correct(q):
    """「手動・自前実装」が正解になっている問題（公式には11.8%ある）"""
    return any(o.get("correct") and BY_HAND.search(o.get("text", "")) for o in q["options"])


# 問題文から拾う特徴語。一般語は除く
TERM = re.compile(r"[A-Z][A-Za-z0-9]{2,}(?:\s+[A-Z][A-Za-z0-9]+){0,2}")
COMMON = {"AWS", "Amazon", "The", "This", "IAM", "VPC", "API", "EC2", "S3"}


def keyword_leak(q):
    """問題文の特徴語が、正解肢にだけ出ていないか（文字列照合で解けてしまう）"""
    qt = {m.group(0) for m in TERM.finditer(q.get("question", ""))} - COMMON
    if not qt:
        return False
    cor = " ".join(o.get("text", "") for o in q["options"] if o.get("correct"))
    wrong = " ".join(o.get("text", "") for o in q["options"] if not o.get("correct"))
    hit = {t for t in qt if t in cor}
    return bool(hit) and not any(t in wrong for t in hit)


def main():
    off, mine = load()
    rows = []
    for label, qs in (("公式", off), ("自作", mine)):
        n = len(qs)
        sm = [q for q in qs if strawman(q)]
        bh = [q for q in qs if by_hand_correct(q)]
        kl = [q for q in qs if keyword_leak(q)]
        rows.append((label, n, len(sm), len(bh), len(kl)))

    print("=" * 76)
    print(" 問題文を読むだけで切れる誤答（消去法が成立する最大の原因）")
    print("=" * 76)
    print()
    print("%-6s %6s %24s %22s %18s" % ("出典", "問数", "制約を裏返しただけの誤答", "手動が正解になる問題", "キーワード直結"))
    for label, n, sm, bh, kl in rows:
        print("%-6s %6d %20d問(%2d%%) %16d問(%2d%%) %12d問(%2d%%)"
              % (label, n, sm, 100 * sm // n, bh, 100 * bh // n, kl, 100 * kl // n))

    o, m = rows[0], rows[1]
    print()
    ng = 0
    if m[2] * 100 // m[1] > o[2] * 100 // o[1] + 5:
        ng += 1
        print("  要確認: 制約を裏返しただけの誤答が公式より多い")
    if m[3] * 100 // m[1] + 5 < o[3] * 100 // o[1]:
        ng += 1
        print("  要確認: 「手動が正解」の問題が少なすぎる")
        print("          → 『手動と書いてあれば誤答』というメタ規則で解けてしまう")
    if m[4] * 100 // m[1] > o[4] * 100 // o[1] + 5:
        ng += 1
        print("  要確認: 問題文の語が正解肢にだけ出ている問題が多い")

    # 対象を書き出す（修正作業で使う）
    out = {
        "strawman": [{"id": q["id"], "exam": q["exam"], "letters": strawman(q)}
                     for q in mine if strawman(q)],
        "keyword_leak": [{"id": q["id"], "exam": q["exam"]} for q in mine if keyword_leak(q)],
    }
    p = BASE / "資料" / "生成" / "_strawman.json"
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  対象の一覧: 資料/生成/_strawman.json")
    print("    制約を裏返した誤答: %d問 / キーワード直結: %d問"
          % (len(out["strawman"]), len(out["keyword_leak"])))
    per = Counter(x["exam"] for x in out["strawman"])
    print("    資格別(制約を裏返した誤答):", dict(sorted(per.items(), key=lambda x: -x[1])))
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
