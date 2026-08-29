# -*- coding: utf-8 -*-
"""問題の中身を、難易度・分量以外の観点で点検する

これまで測ってきたのは「分量」と「当てやすさ」だけだった。
それ以外にも、試験対策として使えるかを左右する要素がある:

  1. 重複        … 同じ論点の問題が何度も出ると、問題数の割に学べる範囲が狭い
  2. 出題形式    … 複数選択(2つ選べ/3つ選べ)の比率が本番とずれていないか
  3. 古い情報    … 提供終了・新規受付終了のサービスを正解として問うと、学習の役に立たない
  4. 出題の偏り  … 同じサービスばかり問われていないか

いずれも公式模試を基準にする。
"""
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"

# 提供終了・新規受付終了・後継へ移行したもの。
# 正解として問うと受験者が誤った知識を持つため、出てきたら確認する。
#
# 名前が似ているだけの現役サービスを拾わないよう、除外語を併記する。
# 実際に踏んだ誤検出:
#   - CodeStar Connections は CodeConnections に改称された現役サービス（CodeStar本体とは別物）
#   - Snowball Edge Storage Optimized は提供中（終了したのは Compute Optimized と Snowcone）
STALE = {
    "Elasticsearch Service": ("OpenSearch Service に改称", []),
    "Data Pipeline": ("提供終了", []),
    "OpsWorks": ("提供終了", []),
    "SimpleDB": ("新規利用不可", []),
    "CodeStar": ("提供終了", ["CodeStar Connections", "CodeConnections"]),
    "Cloud Directory": ("新規受付終了", []),
    "CodeCommit": ("新規顧客の受付を終了", []),
    "Kendra": ("メンテナンスモード・新規受付終了", []),
    "Pinpoint": ("提供終了予定", []),
    "Forecast": ("新規受付終了", ["Forecast Horizon"]),
    "Snowcone": ("提供終了", []),
    "Snowball Edge Compute Optimized": ("提供終了", []),
}


def load():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig"]


def check_duplicates(mine):
    """問題文が酷似しているものを探す

    資格ごとに閉じて探すと、資格をまたいだ重複を見逃す。
    実際に SAP-C02 と DEA-C01 で、ほぼ同一の Lake Formation の設計問題が見つかった。
    別の試験でも、同じ論点を2回解くだけになるので学べる範囲が狭まる。
    """
    hits = []
    groups = [[q for q in mine if q["exam"] == ex] for ex in sorted({q["exam"] for q in mine})]
    groups.append(mine)   # 全資格を横断した比較も行う
    seen = set()
    for qs in groups:
        for i, a in enumerate(qs):
            for b in qs[i + 1:]:
                if a["id"] == b["id"] or (a["id"], b["id"]) in seen:
                    continue
                # 全組み合わせは重いので、先頭が近いものだけ詳しく比べる
                if a["question"][:20] != b["question"][:20] and \
                   SequenceMatcher(None, a["question"][:60], b["question"][:60]).ratio() < 0.7:
                    continue
                r = SequenceMatcher(None, a["question"], b["question"]).ratio()
                if r >= 0.85:
                    seen.add((a["id"], b["id"]))
                    tag = a["exam"] if a["exam"] == b["exam"] else "資格をまたぐ"
                    hits.append((tag, a["id"], b["id"], round(r, 2)))
    return hits


def check_same_topic(mine):
    """文面は違うが「正解の構成」が同じ問題を探す

    文字列の類似度だけでは、言い回しを変えた同一論点を見逃す。
    実際に SAP-C02 と DEA-C01 で、どちらも
    「Lake Formation のクロスアカウント列レベル許可 + リソースリンク + Athena」を
    正解とする問題が見つかった(文字列の一致度は0.39しかなく、既存の検査では素通りしていた)。
    """
    TERM = re.compile(r"(?:Amazon|AWS)\s+[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2}"
                      r"|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+")
    def key(q):
        t = " ".join(o.get("text", "") for o in q.get("options", []) if o.get("correct"))
        return {m.group(0).replace("Amazon ", "").replace("AWS ", "").strip()
                for m in TERM.finditer(t)}

    keys = [(q, key(q)) for q in mine if q.get("options")]
    hits = []
    for i, (a, ka) in enumerate(keys):
        if len(ka) < 3:      # 固有名詞が少ない問題は比べても意味がない
            continue
        for b, kb in keys[i + 1:]:
            if len(kb) < 3:
                continue
            j = len(ka & kb) / len(ka | kb)
            if j >= 0.6:
                hits.append((a["id"], b["id"], round(j, 2), sorted(ka & kb)[:4]))
    return hits


def check_shape(off, mine):
    """「正解数 × 選択肢数」の組み合わせを公式と比べる

    複数選択の比率だけを見ていると、公式が採用していない形を見逃す。
    実際、公式1070問は 1正解4肢 / 2正解5肢 / 3正解6肢 の3種類しかないのに、
    自作には「1正解5肢」が166問あった。4つ目の誤答が水増しになりやすい形。
    """
    def shape(q):
        nc = q.get("n_correct") or sum(1 for x in q["options"] if x.get("correct"))
        return (nc, len(q["options"]))
    co = Counter(shape(q) for q in off if q.get("options"))
    cm = Counter(shape(q) for q in mine if q.get("options"))
    rows, ng = [], []
    for k in sorted(set(co) | set(cm)):
        rows.append((k, co[k], cm[k]))
        if co[k] == 0 and cm[k] >= 10:
            ng.append((k, cm[k]))
    return rows, ng


def check_format(off, mine):
    """複数選択の比率を公式と比べる"""
    rows = []
    for ex in sorted({q["exam"] for q in mine}):
        o = [q for q in off if q.get("exam") == ex and q.get("type", "choice") == "choice"]
        m = [q for q in mine if q["exam"] == ex and q.get("type", "choice") == "choice"]
        if not o:
            continue
        oc = Counter(q.get("n_correct", 1) for q in o)
        mc = Counter(q.get("n_correct", 1) for q in m)
        rows.append((ex, len(o), oc, len(m), mc))
    return rows


def check_stale(mine):
    """提供終了・受付終了のサービスが正解として問われていないか"""
    hits = []
    for q in mine:
        cor = " ".join(o.get("text", "") for o in q.get("options", []) if o.get("correct"))
        for name, (why, excludes) in STALE.items():
            if not re.search(re.escape(name), cor):
                continue
            # 現役の別サービスを名前の一部で拾っていないか確かめる
            masked = cor
            for e in excludes:
                masked = masked.replace(e, "")
            if re.search(re.escape(name), masked):
                hits.append((q["exam"], q["id"], name, why))
    return hits


SVC_RE = re.compile(r"(?:Amazon|AWS)\s+([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2})")


def _bias_share(qs):
    """正解肢に出てくるサービスのうち、上位3種が占める割合"""
    c = Counter()
    for q in qs:
        for o in q.get("options", []):
            if o.get("correct"):
                for m in SVC_RE.finditer(o.get("text", "")):
                    c[m.group(1).strip()] += 1
    if not c:
        return None, []
    top = c.most_common(3)
    return 100 * sum(n for _, n in top) // max(1, sum(c.values())), top


def check_service_bias(mine, off):
    """同じサービスばかり正解になっていないか。

    **絶対値では判定しない。** 公式模試そのものに偏りがあり、その度合いは資格ごとに
    大きく違う(SAP-C02 13% に対し AIP-C01 48%)。以前はここを share>=30 の
    決め打ちで判定していたため、公式 36.5% に対して自作 33.8% の DEA-C01 を
    「偏りが大きい」と誤検出していた。指摘された側が不要な作り直しに入る危険があった。
    """
    rows = []
    for ex in sorted({q["exam"] for q in mine}):
        qs = [q for q in mine if q["exam"] == ex]
        share, top = _bias_share(qs)
        if share is None:
            continue
        off_share, _ = _bias_share([q for q in off if q.get("exam") == ex])
        rows.append((ex, len(qs), top, share, off_share))
    return rows


def main():
    off, mine = load()
    ng = 0
    # 何が引っかかったかを最後に1行で出す。audit_all.py は各スクリプトの
    # 「最後の行」を要約として拾うため、ここが無いと無関係な行(以前はサービスの偏りの
    # 最終行)が要確認の理由として表示され、誤った作業に入る危険がある。
    reasons = []

    print("=" * 74)
    print("1. 内容が重複している問題")
    dup = check_duplicates(mine)
    if dup:
        ng += 1
        reasons.append("重複%d組" % len(dup))
        for ex, a, b, r in dup[:20]:
            print("  %-9s %s ≒ %s (一致度 %.0f%%)" % (ex, a, b, r * 100))
        print("  計 %d 組" % len(dup))
    else:
        print("  なし")

    print()
    print("=" * 74)
    print("1b. 文面は違うが正解の構成が同じ問題")
    same = check_same_topic(mine)
    if same:
        ng += 1
        reasons.append("正解の構成が同じ%d組" % len(same))
        for a, b, j, common in same[:15]:
            print("  %s ≒ %s (共通 %.0f%%: %s)" % (a, b, j * 100, " / ".join(common)))
        print("  計 %d 組" % len(same))
    else:
        print("  なし")

    print()
    print("=" * 74)
    print("1c. 出題の形（正解数 × 選択肢数）")
    rows, shape_ng = check_shape(off, mine)
    for (nc, n), a, b in rows:
        mark = "   ★公式にない形" if a == 0 and b >= 10 else ""
        print("  %d正解 / %d肢   公式 %4d問   自作 %4d問%s" % (nc, n, a, b, mark))
    if shape_ng:
        ng += 1
        reasons.append("公式にない出題の形")

    print()
    print("=" * 74)
    print("2. 複数選択の比率(公式 → 自作)")
    fmt_ng = []
    for ex, no, oc, nm, mc in check_format(off, mine):
        def pct(c, n, k):
            return 100 * c.get(k, 0) // max(1, n)
        line = "  %-9s 1つ選択 %3d%%→%3d%%   2つ選択 %3d%%→%3d%%   3つ選択 %3d%%→%3d%%" % (
            ex, pct(oc, no, 1), pct(mc, nm, 1), pct(oc, no, 2), pct(mc, nm, 2),
            pct(oc, no, 3), pct(mc, nm, 3))
        # 公式に3つ選択があるのに自作に無い、などのずれを目立たせる
        gap = max(abs(pct(oc, no, k) - pct(mc, nm, k)) for k in (1, 2, 3))
        if gap >= 12:
            fmt_ng.append(ex)
        print(line + ("   ★ずれ%dpt" % gap if gap >= 12 else ""))
    if fmt_ng:
        # 本番と出題の形が違うと、演習の感覚がずれる。件数だけでなく資格名を残す
        ng += 1
        reasons.append("複数選択の比率のずれ(%s)" % "、".join(fmt_ng))

    print()
    print("=" * 74)
    print("3. 提供終了・新規受付終了のサービスが正解になっている問題")
    stale = check_stale(mine)
    if stale:
        ng += 1
        reasons.append("提供終了サービスが正解%d問" % len(stale))
        seen = set()
        for ex, qid, name, why in stale:
            if (ex, name) in seen:
                continue
            seen.add((ex, name))
            print("  %-9s %-22s %s (%s)" % (ex, qid, name, why))
        print("  計 %d 問" % len(stale))
    else:
        print("  なし")

    print()
    print("=" * 74)
    print("4. 正解に出てくるサービスの偏り(上位3種が占める割合)")
    print("   公式模試にも偏りがあるため、絶対値ではなく公式との差で見る")
    bias_ng = []
    for ex, n, top, share, off_share in check_service_bias(mine, off):
        if off_share is None:
            mark = ""
            cmp_ = "  公式 --  "
        else:
            gap = share - off_share
            mark = "   ★公式より偏り大 %+dpt" % gap if gap >= 8 else ""
            cmp_ = "  公式 %2d%%" % off_share
            if mark:
                ng += 1
                bias_ng.append(ex)
        print("  %-9s %3d問  %-44s 自作 %2d%%%s%s" % (
            ex, n, " / ".join("%s(%d)" % (s, c) for s, c in top), share, cmp_, mark))
    if bias_ng:
        reasons.append("公式より偏りが大きい(%s)" % "、".join(bias_ng))

    print()
    print("=" * 74)
    # audit_all.py はこの最終行を要約として拾う
    print("要確認: " + " / ".join(reasons) if reasons else "要確認なし")
    return ng


if __name__ == "__main__":
    sys.exit(main())
