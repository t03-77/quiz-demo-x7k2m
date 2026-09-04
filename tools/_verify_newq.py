# -*- coding: utf-8 -*-
"""新規作成した問題ファイルを、既存問題・公式と突き合わせて検証する。

新問は既存の改善作業とは別の壊し方をする（id衝突、domainの新設、
重なりの作りすぎ、公式と違う分量）。ビルド前にここで弾く。

使い方:
    python tools/_verify_newq.py                    # 資料/生成/*_topic1.json と *_s9.json を全部
    python tools/_verify_newq.py CLF-C02_orig_topic1.json
"""
import glob
import json
import os
import re
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")
STEM_WORD = re.compile(r"[A-Za-z][A-Za-z0-9 ]+|[ァ-ヶー]{3,}")
ID_FMT = re.compile(r"^[A-Z]{3}-C\d{2}_orig_\d+$")
REQUIRED = ["id", "exam", "set", "type", "domain", "level", "question", "n_correct", "options"]


def overlap(q):
    sets = [set(WORD.findall(o.get("text", ""))) for o in q.get("options", []) if o.get("text")]
    sets = [s for s in sets if s]
    if len(sets) < 2:
        return None
    return statistics.mean([len(sets[i] & sets[j]) / len(sets[i] | sets[j])
                            for i in range(len(sets)) for j in range(i + 1, len(sets))])


def longest_is_correct(qs):
    hi = tot = 0
    for q in qs:
        op = q.get("options") or []
        cor = [len(o["text"]) for o in op if o.get("correct")]
        wr = [len(o["text"]) for o in op if not o.get("correct")]
        if not cor or not wr:
            continue
        tot += 1
        m = max(cor + wr)
        if max(cor) == m and max(wr) != m:
            hi += 1
    return hi / tot * 100 if tot else 0


def main():
    targets = sys.argv[1:]
    if not targets:
        targets = [os.path.basename(p) for p in
                   sorted(glob.glob(str(GEN / "*_topic1.json")) + glob.glob(str(GEN / "*_s9.json")))]
    off = json.load(open(OFFICIAL, encoding="utf-8"))["questions"]
    ng = 0

    for name in targets:
        path = GEN / name
        try:
            new = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("[NG] %s: JSONが読めない %s" % (name, e))
            ng += 1
            continue
        exam = new[0]["exam"]
        print("=" * 70)
        print(" %s (%s / %d問)" % (name, exam, len(new)))
        print("=" * 70)

        others, exist_ids, doms = [], set(), set()
        for f in glob.glob(str(GEN / "*_orig*.json")):
            if "_bak" in f or os.path.basename(f) == name:
                continue
            try:
                qs = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            for q in qs:
                exist_ids.add(q.get("id"))
                if q.get("exam") == exam and q.get("set") == "orig":
                    others.append(q)
                    doms.add(q.get("domain"))

        ids = [q.get("id") for q in new]
        checks = [
            ("id重複(既存と)", sorted(set(ids) & exist_ids)),
            ("id重複(ファイル内)", sorted({i for i in ids if ids.count(i) > 1})),
            ("id書式", [i for i in ids if not ID_FMT.match(str(i))]),
            ("必須フィールド", [q.get("id") for q in new if any(k not in q for k in REQUIRED)]),
            ("n_correct整合", [q["id"] for q in new
                             if sum(1 for o in q["options"] if o.get("correct")) != q.get("n_correct")]),
            ("解説の有無", [q["id"] for q in new if any(not o.get("explanation") for o in q["options"])]),
            ("domain(既存にない)", sorted({q.get("domain") for q in new} - doms)),
        ]
        for label, bad in checks:
            if bad:
                ng += 1
            print("  %-22s %s" % (label, ("★ " + str(bad[:3])) if bad else "OK"))

        offx = [q for q in off if q.get("exam") == exam and q.get("set") in ("exam", "pretest")]
        ov_new = [v for v in (overlap(q) for q in new) if v is not None]
        ov_off = [v for v in (overlap(q) for q in offx) if v is not None]
        ov_old = [v for v in (overlap(q) for q in others) if v is not None]
        m_new, m_off = statistics.mean(ov_new), statistics.mean(ov_off)
        over = m_new > m_off * 1.25
        ng += 1 if over else 0
        print("  %-22s 新問 %.3f / 公式 %.3f / 既存 %.3f%s" % (
            "肢の語の重なり", m_new, m_off,
            statistics.mean(ov_old) if ov_old else 0, "  ★超過" if over else ""))

        # 設定断片(JSON/ログ)入りの問題は、公式でも極端に長い(中央734字)。
        # 公式の全問(221字)と比べると必ず乖離判定になるので、断片入り同士で比べる。
        CODE = re.compile(r"[{}]|\"[A-Za-z]+\"\s*:|Effect\s*[:=]|arn:aws|<[a-z]+>|\n\s{4,}\S")
        if sum(1 for q in new if CODE.search(q["question"])) >= len(new) * 0.6:
            base = [q for q in off if CODE.search(q.get("question", ""))
                    and q.get("set") in ("exam", "pretest")]
            if base:
                offx_len = base
                print("  %-22s 設定断片入りの問題として公式%d問と比較" % ("(注)", len(base)))
            else:
                offx_len = offx
        else:
            offx_len = offx
        qn = statistics.median([len(q["question"]) for q in new])
        qo = statistics.median([len(q["question"]) for q in offx_len])
        ratio = qn / qo * 100
        far = not (70 <= ratio <= 145)
        ng += 1 if far else 0
        print("  %-22s 新問 %d字 / 公式 %d字 (%.0f%%)%s" % (
            "問題文の分量", qn, qo, ratio, "  ★乖離" if far else ""))

        ln, lo = longest_is_correct(new), longest_is_correct(offx)
        gap = abs(ln - lo)
        ng += 1 if gap > 15 else 0
        print("  %-22s 新問 %.0f%% / 公式 %.0f%%%s" % (
            "最長が正解", ln, lo, "  ★差%.0fpt" % gap if gap > 15 else ""))

        # 一般語は偶然どちらかに寄るだけで手がかりにならない。
        # 2026-09-04: 「アクセス」「アプリケーション」「デプロイ」だけで3問が誤検出されたため除外。
        GENERIC = {"アクセス", "アプリケーション", "デプロイ", "サービス", "データ", "ユーザー",
                   "リクエスト", "モデル", "設定", "システム", "エンドポイント", "コンテンツ",
                   "セキュリティ", "パフォーマンス", "コスト", "トレーニング", "プロンプト",
                   "シーケンス", "インスタンス", "ワークフロー", "パラメータ", "ドキュメント",
                   "レスポンス", "アカウント", "リソース", "クエリ", "ジョブ", "ポリシー"}
        leaks = []
        for q in new:
            stem = {w.strip() for w in STEM_WORD.findall(q["question"])
                    if len(w.strip()) > 3 and w.strip() not in GENERIC}
            cor = [o for o in q["options"] if o.get("correct")]
            wr = [o for o in q["options"] if not o.get("correct")]
            for w in stem:
                if any(w in o["text"] for o in cor) and not any(w in o["text"] for o in wr):
                    leaks.append("%s(%s)" % (q["id"], w))
                    break
        if leaks:
            ng += 1
        print("  %-22s %s" % ("キーワード直結", ("★ " + str(leaks[:3])) if leaks else "OK"))
        print()

    print("=" * 70)
    print(" 要確認: %d件" % ng if ng else " すべて基準内")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
