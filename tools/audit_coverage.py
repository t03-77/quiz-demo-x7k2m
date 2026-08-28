# -*- coding: utf-8 -*-
"""出題範囲と出題傾向が公式模試に近いかを測る

これまで測ってきたのは「形式」と「当てやすさ」だった。
このスクリプトは**何がどれだけ問われているか**を公式と比べる。

  1. 範囲   … 公式で問われるサービスを取りこぼしていないか
  2. 傾向   … 出現頻度の分布が公式と似ているか（順位相関）
  3. 偏り   … 公式では頻出なのに自作では少ないもの／その逆
  4. 論点   … 正解として問われる構成（サービス＋機能の組）の重なり

「サービスが1回でも出れば良い」ではなく、**出る割合まで**合っているかを見る。
公式で15%を占めるサービスが自作で1%なら、範囲は埋まっていても傾向は違う。

使い方: python tools/audit_coverage.py [EXAM_ID]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OFFICIAL = BASE / "資料" / "変換済み" / "questions_all.json"
ORIG = BASE / "data" / "orig.js"

# サービス名。略称と正式名を1つにまとめるための対応表
ALIAS = {
    "Simple Storage Service": "S3", "Elastic Compute Cloud": "EC2",
    "Simple Queue Service": "SQS", "Simple Notification Service": "SNS",
    "Elastic Block Store": "EBS", "Elastic File System": "EFS",
    "Key Management Service": "KMS", "Identity and Access Management": "IAM",
    "Elastic Container Service": "ECS", "Elastic Kubernetes Service": "EKS",
    "Elastic Container Registry": "ECR", "Relational Database Service": "RDS",
    "Application Load Balancer": "ALB", "Network Load Balancer": "NLB",
    "Database Migration Service": "DMS", "Resource Access Manager": "RAM",
    "Data Firehose": "Firehose", "Kinesis Data Firehose": "Firehose",
    "SageMaker AI": "SageMaker", "OpenSearch Service": "OpenSearch",
}
SVC = re.compile(r"(?:Amazon|AWS)\s+([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,3})"
                 r"|\b(S3|EC2|SQS|SNS|EBS|EFS|KMS|IAM|ECS|EKS|ECR|RDS|ALB|NLB|VPC|DMS|RAM|EMR|WAF)\b")
NOISE = {"Identity", "Resource Name", "X", "Linux", "Windows", "Region", "Regions",
         "Management Console", "Cloud", "Account", "Accounts", "Free Tier", "Support",
         "Well", "Marketplace", "Partner Network", "SDK", "CLI", "Certificate"}


def norm(s):
    s = s.strip()
    for k, v in ALIAS.items():
        if s.startswith(k):
            return v
    return s


def raw_services(text):
    """「Amazon X」「AWS X」の形から名前を拾う。語彙を作るときに使う"""
    out = set()
    for m in SVC.finditer(text or ""):
        s = norm(m.group(1) or m.group(2) or "")
        if s and s not in NOISE and len(s) > 1:
            out.add(s)
    return out


# 公式から作った語彙。自作を調べるときは、この名前が本文に出るかで判定する。
# 「Amazon Athena」の形でしか拾えないと、「Athena」とだけ書かれた問題を
# 「無い」と誤検出する（実際にそれで9問を見落とした）
VOCAB = []


def build_vocab(off):
    v = set()
    for q in off:
        v |= raw_services(correct_text(q))
    # 長い名前から先に照合する（"S3 Glacier" を "S3" より優先）
    VOCAB[:] = sorted(v, key=len, reverse=True)


def services(text):
    t = text or ""
    return {s for s in VOCAB if re.search(r"(?<![A-Za-z0-9])" + re.escape(s) + r"(?![A-Za-z0-9])", t)}


def load():
    d = json.load(open(OFFICIAL, encoding="utf-8"))
    off = d.get("questions", d) if isinstance(d, dict) else d
    off = [q for q in off if q.get("set") in ("exam", "pretest") and q.get("options")]
    js = open(ORIG, encoding="utf-8").read()
    mine = json.loads(js[js.index("["): js.rindex("]") + 1])
    return off, [q for q in mine if q.get("set") == "orig" and q.get("options")]


def correct_text(q):
    """正解として問われている構成。問題文ではなく正解肢を見る"""
    return " ".join(o.get("text", "") for o in q["options"] if o.get("correct"))


def dist(qs):
    """サービスごとの出現率（%）"""
    c = Counter()
    for q in qs:
        for s in services(correct_text(q)):
            c[s] += 1
    n = max(1, len(qs))
    return {k: 100 * v / n for k, v in c.items()}, c


def spearman(a, b, keys):
    """順位相関。出現の多い順がどれだけ似ているか（1に近いほど似ている）"""
    ra = {k: i for i, k in enumerate(sorted(keys, key=lambda k: -a.get(k, 0)))}
    rb = {k: i for i, k in enumerate(sorted(keys, key=lambda k: -b.get(k, 0)))}
    n = len(keys)
    if n < 3:
        return 0.0
    d2 = sum((ra[k] - rb[k]) ** 2 for k in keys)
    return 1 - 6 * d2 / (n * (n * n - 1))


def topics(qs):
    """論点＝正解肢に一緒に出てくるサービスの組。何と何を組み合わせる構成かを見る"""
    c = Counter()
    for q in qs:
        s = sorted(services(correct_text(q)))
        if len(s) >= 2:
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    c[(s[i], s[j])] += 1
        elif s:
            c[(s[0],)] += 1
    return c


def main():
    off, mine = load()
    exams = [sys.argv[1]] if len(sys.argv) > 1 else sorted({q["exam"] for q in mine})

    print("=" * 78)
    print(" 出題範囲と出題傾向が公式模試に近いか")
    print("=" * 78)
    print()
    print("%-9s %8s %10s %12s %14s" % ("資格", "範囲の穴", "順位相関", "論点の重なり", "傾向のずれ"))
    print("-" * 78)

    ng = []
    detail = {}
    for ex in exams:
        o = [q for q in off if q.get("exam") == ex]
        m = [q for q in mine if q["exam"] == ex]
        if not o or not m:
            continue
        build_vocab(o)   # その資格の公式問題から語彙を作ってから比べる
        do, co = dist(o)
        dm, cm = dist(m)

        # 1. 範囲の穴: 公式で2回以上問われるのに自作に一度も出ないサービス
        holes = [s for s, c in co.items() if c >= 2 and s not in dm]

        # 2. 順位相関: どちらかで上位に来るサービスで比べる
        keys = sorted(set([s for s, c in co.items() if c >= 2]) |
                      set([s for s, c in cm.items() if c >= 2]))
        rho = spearman(do, dm, keys) if len(keys) >= 3 else 0

        # 3. 論点の重なり: 正解肢に共起するサービスの組がどれだけ一致するか
        to, tm = topics(o), topics(m)
        common = set(to) & set(tm)
        jac = len(common) / max(1, len(set(to) | set(tm)))

        # 4. 傾向のずれ: 出現率の差が大きいサービス
        gaps = sorted(((abs(do.get(s, 0) - dm.get(s, 0)), s) for s in keys), reverse=True)[:3]
        detail[ex] = (holes, gaps, do, dm)

        mark = ""
        if holes or rho < 0.3:
            mark = "  ★"
            ng.append(ex)
        print("%-9s %6d件 %10.2f %11.0f%% %s" % (
            ex, len(holes), rho, jac * 100,
            " / ".join("%s %+.0fpt" % (s, dm.get(s, 0) - do.get(s, 0)) for _, s in gaps) + mark))

    print()
    print("  順位相関 … 出題の多い順がどれだけ似ているか（1に近いほど公式と同じ傾向）")
    print("  論点の重なり … 正解に出てくるサービスの組み合わせの一致率")
    print("  傾向のずれ … 出現率の差が大きい上位3件（+は自作が多い、−は自作が少ない）")

    if ng:
        print()
        print("要確認:")
        for ex in ng:
            holes, gaps, do, dm = detail[ex]
            if holes:
                print("  %-9s 公式で問われるのに自作に無い: %s" % (ex, ", ".join(holes[:8])))
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
