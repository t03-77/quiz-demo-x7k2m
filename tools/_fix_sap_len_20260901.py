# -*- coding: utf-8 -*-
"""overlap第1弾の副作用修正:
(1) SAP-C02「最長は誤答」の癖(75%; 公式60%)を、最小差13問の最長誤答肢の冗長語削除で公式並みに戻す
(2) DOP-C02_orig_065 のキーワード直結(CloudWatch が正解肢のみ)を誤答Bへの自然な追記で解消
すべて誤答肢 text の置換のみ。意味は変えない(解説との整合は保たれる)。"""
import json
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# (id, letter, old_fragment, new_fragment)
EDITS = [
    ("SAP-C02_orig_034", "B", "をシングル AZ 構成でデプロイし", "をシングル AZ でデプロイし"),
    ("SAP-C02_orig_034", "C", "マウントターゲットでデプロイし", "マウントターゲットで作成し"),
    ("SAP-C02_orig_052", "B", "経由でそのエンドポイントを呼び出す", "経由でエンドポイントを呼び出す"),
    ("SAP-C02_orig_305", "F", "個別に接続して、VPC ごとにルートテーブルの設定を行う", "個別に接続し、VPC ごとにルートテーブルを設定する"),
    ("SAP-C02_orig_025", "D", "プライマリとして読み書きさせて同期する", "プライマリとして読み書きさせる"),
    ("SAP-C02_orig_025", "E", "レプリカにのみ書き込むようにする", "レプリカにのみ書き込ませる"),
    ("SAP-C02_orig_053", "B", "EC2 インスタンス上で稼働させるカスタムコンシューマーで", "EC2 インスタンスのカスタムコンシューマーで"),
    ("SAP-C02_orig_097", "B", "リージョンと同じ AWS API と IAM で運用する", "リージョンと同じ API と IAM で運用する"),
    ("SAP-C02_orig_097", "B", "工場からの通信レイテンシーを短縮し", "工場からのレイテンシーを短縮し"),
    ("SAP-C02_orig_097", "D", "AWS Snowball Edge Compute Optimized デバイスを工場に常設し", "AWS Snowball Edge Compute Optimized を工場に常設し"),
    ("SAP-C02_orig_024", "D", "パブリックエンドポイントへ NAT ゲートウェイ経由でアクセスさせて", "パブリックエンドポイントへ NAT 経由でアクセスさせて"),
    ("SAP-C02_orig_024", "C", "プライベート DNS を有効にして作成する", "プライベート DNS 有効で作成する"),
    ("SAP-C02_orig_030", "B", "各ワークロードアカウントには中央バスへイベントを転送する", "各ワークロードアカウントに中央バスへ転送する"),
    ("SAP-C02_orig_060", "B", "各チームのエンドポイントがイベントを受信して処理する", "各チームのエンドポイントで受信して処理する"),
    ("SAP-C02_orig_007", "C", "容量が回収された際は別のプールから起動し直すことで", "容量回収時は別のプールから起動し直すことで"),
    ("SAP-C02_orig_007", "C", "割引を最大限に活用する", "割引を最大限活用する"),
    ("SAP-C02_orig_007", "D", "バッチ処理のベースライン使用量に対して", "バッチのベースライン使用量に対して"),
    ("SAP-C02_orig_039", "C", "容量あたりの単価を下げて", "容量単価を下げて"),
    ("SAP-C02_orig_039", "C", "容量はそのまま維持する", "容量は維持する"),
    ("SAP-C02_orig_041", "B", "2 本をリンクアグリゲーショングループ (LAG) として束ねて", "リンクアグリゲーショングループ (LAG) で束ねて"),
    ("SAP-C02_orig_041", "B", "回線やポートの障害を吸収する", "回線やポート障害を吸収する"),
    ("SAP-C02_orig_059", "C", "クラスターを作成し、アプリケーションの接続先を", "クラスターを作成し、接続先を"),
    ("SAP-C02_orig_059", "D", "クラスターを作成し、アプリケーションにキャッシュアサイド方式", "クラスターを作成し、キャッシュアサイド方式"),
    ("DOP-C02_orig_065", "B", "詳細モニタリングを有効にして、標準メトリクスの発行間隔を", "詳細モニタリングを有効にして、CloudWatch への標準メトリクスの発行間隔を"),
]

by_id = {}
for qid, letter, old, new in EDITS:
    by_id.setdefault(qid, []).append((letter, old, new))

applied = 0
for f in glob.glob(str(BASE / "資料" / "生成" / "*_orig*.json")):
    if "_bak" in f:
        continue
    data = json.load(open(f, encoding="utf-8"))
    dirty = False
    for q in data:
        if q["id"] not in by_id:
            continue
        for letter, old, new in by_id[q["id"]]:
            o = next(x for x in q["options"] if x["letter"] == letter)
            assert not o["correct"], "正解肢に書き込もうとした: %s %s" % (q["id"], letter)
            assert old in o["text"], "置換元が見つからない: %s %s %r" % (q["id"], letter, old)
            o["text"] = o["text"].replace(old, new)
            applied += 1
            dirty = True
    if dirty:
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
        print("updated:", Path(f).name)
print("applied edits:", applied, "/", len(EDITS))
