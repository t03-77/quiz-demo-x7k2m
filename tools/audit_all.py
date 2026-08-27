# -*- coding: utf-8 -*-
"""全部の点検を一度に走らせ、観点の一覧を出す

このファイルを作った理由:
  これまで、利用者に「この観点は見たか」と指摘されるたびに検査を後追いで作っていた。
  観点がどこにも一覧化されておらず、抜けに自分で気づけなかったのが原因。
  そこで「試験に受かる問題集として満たすべき条件」を先に並べ、
  各条件に検査があるか / 未検査かを、結果と一緒に必ず表示するようにした。

  **機械で測れない観点も「未検査」として必ず出す。** 出さないと、
  検査が全部通ったときに「全部問題なし」と誤解する。

使い方: python tools/audit_all.py
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"

# 本番の出題数(問題数が何回分にあたるかの計算に使う)
EXAM_N = {"CLF-C02": 65, "AIF-C01": 65, "SAA-C03": 65, "DVA-C02": 65, "SOA-C03": 65,
          "DEA-C01": 65, "MLA-C01": 65, "SCS-C03": 65, "AIP-C01": 65,
          "SAP-C02": 75, "DOP-C02": 75}

# 外部スクリプトに任せている検査。(観点, コマンド, 合格とみなす終了コード)
EXTERNAL = [
    ("データの整合(ID重複・スキーマ)", ["node", "tools/smoke_test.js"], 0),
    ("解説と正誤フラグの矛盾", [sys.executable, "-X", "utf8", "tools/audit_consistency.py"], 0),
    ("ドメイン配分が公式試験ガイドと合うか", [sys.executable, "-X", "utf8", "tools/audit_domains.py"], 0),
    ("解説の分量が公式模試の水準か", [sys.executable, "-X", "utf8", "tools/audit_explanations.py"], 0),
    ("当てやすさ(正解が最長など)", [sys.executable, "-X", "utf8", "tools/audit_difficulty.py"], 0),
    ("内容面(重複・出題形式・古い情報・偏り)", [sys.executable, "-X", "utf8", "tools/audit_content.py"], 0),
]

# 機械では判定できない観点。人またはAIによる読み込みが要る。
# 「検査が全部通った=問題なし」と誤解しないよう、必ず表示する。
MANUAL = [
    ("解説の技術的な正確性(全数)", "公式ドキュメントで精読したのは既存101問+新規約60問。残りは機械的検査のみ"),
    ("問題文の日本語としての自然さ", "未検査。機械翻訳調・不自然な言い回しは検出していない"),
    ("正解そのものの妥当性", "audit_consistencyは解説との矛盾しか見ない。正解が本当に最適解かは未検証"),
    ("学習効果(実際に合格率が上がるか)", "検証不能。公式模試との一致度を代理指標にしている"),
]


def load():
    """選択式以外(マッチング・並び替え)も含めて返す。

    ここで options のある問題だけに絞ると、分量の比較で公式側の分布が変わり、
    下限値がずれて誤判定になる(実際にそれで「下限割れ15問」と誤報した)。
    選択肢が要る検査は、各関数の中で絞ること。
    """
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig"]


def with_options(qs):
    return [q for q in qs if q.get("options")]


def xorshift(seed):
    h = 2166136261
    for c in seed:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    state = [h]

    def rnd():
        h2 = state[0]
        h2 ^= (h2 << 13) & 0xFFFFFFFF
        h2 ^= h2 >> 17
        h2 ^= (h2 << 5) & 0xFFFFFFFF
        state[0] = h2 & 0xFFFFFFFF
        return state[0] / 4294967296
    return rnd


def shuffled(arr, seed):
    """index.html の shuffled() と同じ並べ替え。表示時の正解位置を再現する"""
    a = list(arr)
    r = xorshift(seed)
    for i in range(len(a) - 1, 0, -1):
        j = int(r() * (i + 1))
        a[i], a[j] = a[j], a[i]
    return a


def answer_position(off, mine):
    """正解の位置が偏っていないか(アプリの既定=シャッフルON で判定)"""
    off, mine = with_options(off), with_options(mine)
    L = "ABCDEFGH"
    oc, mc = Counter(), Counter()
    for q in off:
        for o in q["options"]:
            if o.get("correct"):
                oc[o.get("letter")] += 1
    for q in mine:
        for i, o in enumerate(shuffled(q["options"], "opt:" + q["id"])):
            if o.get("correct"):
                mc[L[i]] += 1

    def pct(c):
        t = sum(c.values())
        return {k: round(100 * v / t) for k, v in sorted(c.items())}
    o, m = pct(oc), pct(mc)
    worst = max(m.values()) if m else 0
    ok = worst <= 35   # どれか1つの記号に偏っていたら、その記号を選ぶだけで当たってしまう
    return ok, "公式 %s / 自作 %s" % (o, m)


def raw_answer_position(mine):
    """データ上(シャッフル前)の正解位置。JSONを直接見る人向けの参考値"""
    mine = with_options(mine)
    c = Counter()
    for q in mine:
        for o in q["options"]:
            if o.get("correct"):
                c[o.get("letter")] += 1
    t = sum(c.values())
    m = {k: round(100 * v / t) for k, v in sorted(c.items())}
    worst = max(m.values()) if m else 0
    return worst <= 35, "%s ※アプリは既定でシャッフルするため出題時は解消される" % m


def option_count(off, mine):
    off, mine = with_options(off), with_options(mine)
    o = Counter(len(q["options"]) for q in off)
    m = Counter(len(q["options"]) for q in mine)

    def pct(c):
        t = sum(c.values())
        return {k: round(100 * v / t) for k, v in sorted(c.items())}
    po, pm = pct(o), pct(m)
    gap = max(abs(pm.get(k, 0) - po.get(k, 0)) for k in set(po) | set(pm))
    return gap <= 25, "公式 %s / 自作 %s" % (po, pm)


def question_length(off, mine):
    """問題文の分量が公式模試の下位10%を下回っていないか"""
    import statistics
    bad = 0
    detail = []
    for ex in sorted({q["exam"] for q in mine}):
        o = sorted(len(q.get("question", "")) for q in off if q.get("exam") == ex)
        m = [len(q["question"]) for q in mine if q["exam"] == ex]
        if not o or not m:
            continue
        lo = o[int(len(o) * .1)]
        u = sum(1 for x in m if x < lo)
        bad += u
        detail.append("%s %d%%" % (ex, 100 * statistics.median(m) // statistics.median(o)))
    return bad == 0, "下限割れ %d問 / 公式比 %s" % (bad, " ".join(detail))


def volume(mine):
    """問題数が本番の何回分にあたるか"""
    rows = []
    low = 0
    for ex in sorted({q["exam"] for q in mine}):
        c = sum(1 for q in mine if q["exam"] == ex)
        r = c / EXAM_N.get(ex, 65)
        if r < 1.5:
            low += 1
        rows.append("%s %.1f回" % (ex, r))
    return low == 0, " ".join(rows)


def coverage(mine):
    """図解・用語集がどれだけの問題をカバーしているか"""
    out = []
    dj = BASE / "data" / "diagrams.js"
    if dj.exists():
        src = dj.read_text(encoding="utf-8")
        n = len(re.findall(r"^\s*id:\s*'", src, re.M))
        out.append("図解 %d種" % n)
    gj = BASE / "data" / "glossary.js"
    if gj.exists():
        # 1行のJSONで書かれているため、行頭前提の正規表現では数えられない
        src = gj.read_text(encoding="utf-8")
        try:
            g = json.loads(src[src.index("{"): src.rindex("}") + 1])
            hit = sum(1 for q in mine if any(t in q.get("question", "") for t in g))
            out.append("用語 %d語(%d%%の問題に登場)" % (len(g), 100 * hit // max(1, len(mine))))
        except Exception:
            out.append("用語 読めない")
    au = BASE / "audio"
    if au.exists():
        out.append("音声 %d資格分" % len({p.name.split("_")[0] for p in au.glob("*.mp3")}))
    else:
        out.append("音声 未生成")
    return True, " / ".join(out) if out else "(データなし)"


def run_external(label, cmd, ok_code):
    try:
        p = subprocess.run(cmd, cwd=BASE, capture_output=True, timeout=600)
        out = (p.stdout or b"").decode("utf-8", "replace")
        tail = [l for l in out.strip().splitlines() if l.strip()]
        return p.returncode == ok_code, (tail[-1].strip()[:70] if tail else "")
    except FileNotFoundError:
        return None, "コマンドが見つからない"
    except Exception as e:
        return None, str(e)[:60]


def main():
    off, mine = load()
    print("=" * 78)
    print(" 問題データの点検 — 全観点")
    print(" 対象: 自作 %d問 / 比較基準: 公式模試 %d問" % (len(mine), len(off)))
    print("=" * 78)
    print()

    results = []
    print("【機械で測れる観点】")
    for label, fn in [
        ("問題文の分量が公式模試の水準か", lambda: question_length(off, mine)),
        ("正解の位置の偏り(出題時)", lambda: answer_position(off, mine)),
        ("正解の位置の偏り(データ上)", lambda: raw_answer_position(mine)),
        ("選択肢の数の分布", lambda: option_count(off, mine)),
        ("問題数(本番の何回分か)", lambda: volume(mine)),
        ("補助コンテンツのカバー率", lambda: coverage(mine)),
    ]:
        ok, note = fn()
        results.append(ok)
        print("  %s %-32s %s" % ("OK " if ok else "要確認", label, note))

    for label, cmd, code in EXTERNAL:
        ok, note = run_external(label, cmd, code)
        results.append(ok)
        mark = "OK " if ok else ("要確認" if ok is False else "実行不可")
        print("  %s %-32s %s" % (mark, label, note))

    print()
    print("【機械では測れない観点 — 検査が全部通っても、ここは保証されない】")
    for label, note in MANUAL:
        print("  未検査 %-32s %s" % (label, note))

    print()
    print("=" * 78)
    ng = sum(1 for r in results if r is False)
    if ng:
        print("要確認: %d件。上の該当行を見て、対応する検査を単体で実行すること" % ng)
    else:
        print("機械で測れる観点はすべて基準内。ただし上の「機械では測れない観点」は別途確認が要る")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
