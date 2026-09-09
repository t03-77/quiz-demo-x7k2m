# -*- coding: utf-8 -*-
"""DVA-C02 複文率パッチの生成。(id, letter, 正解肢か, 新テキスト)

いずれも既存の1文を「操作。結果・適用先・条件」の2文に**分割**したもの。
語を足していないので、肢どうしの語の重なりと長さはほぼ変わらない。
問題単位で全肢を組み直しているため「2文なら正解」という手がかりは生まれない。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
P = [
    # --- 002 (5肢/正解2) 決済の二重処理防止 -------------------------------
    ("DVA-C02_orig_002", "A", True, "キューを SQS FIFO キューに移行する。プロデューサーはメッセージ重複排除 ID を設定する。"),
    ("DVA-C02_orig_002", "B", True, "ワーカーアプリケーションで、処理済みの決済 ID を DynamoDB に条件付き書き込みで記録する。既に存在する場合は処理をスキップする冪等性を実装する。"),
    ("DVA-C02_orig_002", "C", False, "キューを SQS FIFO キューに移行する。プロデューサーはメッセージグループ ID を設定する。"),
    ("DVA-C02_orig_002", "D", False, "キューでロングポーリングを有効化する。ReceiveMessage の待機時間は 20 秒に設定する。"),
    ("DVA-C02_orig_002", "E", False, "キューにデッドレターキューを設定する。maxReceiveCount は 1 に設定する。"),
    # --- 003 Kinesis 拡張ファンアウト ------------------------------------
    ("DVA-C02_orig_003", "A", True, "各コンシューマーを拡張ファンアウトコンシューマーとして登録する。SubscribeToShard API でデータを受信する。"),
    ("DVA-C02_orig_003", "B", False, "ストリームのシャード数を 3 倍に増やす。各コンシューマーは GetRecords API でポーリングする。"),
    ("DVA-C02_orig_003", "C", False, "各コンシューマーを拡張ファンアウトコンシューマーとして登録する。GetRecords API でデータを受信する。"),
    ("DVA-C02_orig_003", "D", False, "Kinesis Data Streams を 3 つの Amazon SQS キューに置き換える。コンシューマーごとにキューを割り当てる。"),
    # --- 004 Secrets Manager ---------------------------------------------
    ("DVA-C02_orig_004", "A", True, "認証情報を AWS Secrets Manager に保存し、RDS 用のマネージドローテーションを有効化する。Lambda 関数は実行時にシークレットを取得するように変更する。"),
    ("DVA-C02_orig_004", "B", False, "認証情報を AWS Systems Manager パラメータストアの SecureString パラメータに保存する。Lambda 関数は実行時に取得するように変更する。"),
    ("DVA-C02_orig_004", "C", False, "認証情報を AWS Secrets Manager に保存し、RDS 用のマネージドローテーションを有効化する。デプロイ時に取得した値は Lambda 関数の環境変数へ埋め込む。"),
    ("DVA-C02_orig_004", "D", False, "認証情報を暗号化したファイルとして Lambda のデプロイパッケージに含める。実行時に復号して使用する。"),
    # --- 005 Cognito -----------------------------------------------------
    ("DVA-C02_orig_005", "A", True, "Amazon Cognito ユーザープールでユーザーを認証する。ID プールがユーザープールのトークンと引き換えに一時的な AWS 認証情報を発行するように構成する。"),
    ("DVA-C02_orig_005", "B", False, "Amazon Cognito ユーザープールのみでユーザーを認証する。発行された JWT トークンを使用して S3 API を直接呼び出す。"),
    ("DVA-C02_orig_005", "C", False, "Amazon Cognito ID プールでユーザーを認証する。ユーザープールが ID プールのトークンと引き換えに一時的な AWS 認証情報を発行するように構成する。"),
    ("DVA-C02_orig_005", "D", False, "S3 へのフルアクセス権限を持つ IAM ロールの認証情報をアプリケーションに埋め込む。全ユーザーで共有する。"),
    # --- 011 Lambda レイヤー ---------------------------------------------
    ("DVA-C02_orig_011", "A", True, "共通ライブラリを Lambda レイヤーとしてパッケージ化する。各関数にレイヤーをアタッチする。"),
    ("DVA-C02_orig_011", "B", False, "ライブラリを Amazon S3 に保存する。各関数は実行時にダウンロードする。"),
    ("DVA-C02_orig_011", "C", False, "共通ライブラリを Lambda レイヤーとしてパッケージ化する。各関数の環境変数にレイヤーの ARN を設定する。"),
    ("DVA-C02_orig_011", "D", False, "ライブラリのコードを各関数の環境変数に格納する。各関数は起動時にその値を読み込んで使用する。"),
    # --- 013 API Gateway リクエスト検証 ----------------------------------
    ("DVA-C02_orig_013", "A", True, "リクエストボディの JSON スキーマをモデルとして定義する。メソッドでリクエスト検証を有効化する。"),
    ("DVA-C02_orig_013", "B", False, "Lambda 関数の先頭で入力検証を行う。不正な場合は早期にエラーを返す。"),
    ("DVA-C02_orig_013", "C", False, "AWS WAF のウェブ ACL を API にアタッチする。不正なリクエストをブロックする。"),
    ("DVA-C02_orig_013", "D", False, "レスポンスボディの JSON スキーマをモデルとして定義する。メソッドでリクエスト検証を有効化する。"),
    # --- 015 DynamoDB TTL ------------------------------------------------
    ("DVA-C02_orig_015", "A", True, "テーブルで TTL (有効期限) を有効化する。各アイテムに有効期限のエポック秒を保持する属性を設定する。"),
    ("DVA-C02_orig_015", "B", False, "毎日 Lambda 関数でテーブルを Scan する。期限切れのアイテムは DeleteItem で削除する。"),
    ("DVA-C02_orig_015", "C", False, "アプリケーションがセッション読み取り時に期限切れを検出する。その場で削除する。"),
    ("DVA-C02_orig_015", "D", False, "テーブルで TTL (有効期限) を有効化する。各アイテムに有効期限までの残り秒数を保持する属性を設定する。"),
    # --- 016 (5肢/正解2) S3 -> SNS -> SQS ファンアウト --------------------
    ("DVA-C02_orig_016", "A", True, "Amazon SNS トピックを作成する。S3 イベント通知の送信先として設定する。"),
    ("DVA-C02_orig_016", "B", True, "システムごとに Amazon SQS キューを作成して SNS トピックにサブスクライブする。各システムは自分のキューからメッセージを処理する。"),
    ("DVA-C02_orig_016", "C", False, "S3 イベント通知を 1 つの SQS キューに送信する。3 つのシステムが同じキューを共有して読み取る。"),
    ("DVA-C02_orig_016", "D", False, "各システムが S3 バケットを定期的にポーリングする。新しいオブジェクトを検出したら処理する。"),
    ("DVA-C02_orig_016", "E", False, "システムごとに Amazon SQS キューを作成して S3 イベント通知の送信先に指定する。各システムは自分のキューからメッセージを処理する。"),
    # --- 041 DynamoDB Streams --------------------------------------------
    ("DVA-C02_orig_041", "A", True, "Orders テーブルで DynamoDB Streams を有効化する。ストリームをイベントソースとする AWS Lambda 関数で集計テーブルを更新する。"),
    ("DVA-C02_orig_041", "B", False, "Orders テーブルの前段に Amazon DynamoDB Accelerator (DAX) クラスターを構成する。DAX をイベントソースとする AWS Lambda 関数で集計テーブルを更新する。"),
    ("DVA-C02_orig_041", "C", False, "Orders テーブルで DynamoDB Streams を有効化する。Amazon EventBridge のスケジュールルールで 5 分ごとに起動する AWS Lambda 関数でストリームを読み取って集計テーブルを更新する。"),
    ("DVA-C02_orig_041", "D", False, "Orders テーブルにグローバルセカンダリインデックスを作成する。商品カテゴリをパーティションキーとして集計値を保持する。"),
    # --- 048 Step Functions Express --------------------------------------
    ("DVA-C02_orig_048", "A", True, "Express ワークフローを使用する。必要に応じて実行ログを Amazon CloudWatch Logs に出力する。"),
    ("DVA-C02_orig_048", "B", False, "Standard ワークフローを使用する。必要に応じて実行ログを Amazon CloudWatch Logs に出力する。"),
    ("DVA-C02_orig_048", "C", False, "Step Functions を使用しない。Lambda 関数から次の Lambda 関数を同期的に呼び出すチェーンを実装する。"),
    ("DVA-C02_orig_048", "D", False, "Express ワークフローを使用する。実行ごとの完全な履歴を Step Functions のサービス内で長期保持して確認する。"),
    # --- 056 (5肢/正解2) プライベート API --------------------------------
    ("DVA-C02_orig_056", "A", True, "API のエンドポイントタイプをプライベートに設定する。VPC に execute-api のインターフェイス VPC エンドポイントを作成する。"),
    ("DVA-C02_orig_056", "B", True, "API Gateway のリソースポリシーを設定する。aws:SourceVpce 条件により該当する VPC エンドポイントからのリクエストのみを許可する。"),
    ("DVA-C02_orig_056", "C", False, "API のエンドポイントタイプをプライベートに設定する。VPC に Amazon S3 のゲートウェイ VPC エンドポイントを作成する。"),
    ("DVA-C02_orig_056", "D", False, "エンドポイントタイプはエッジ最適化のままとする。リソースポリシーで aws:SourceIp 条件により社内 IP アドレスからのリクエストのみを許可する。"),
    ("DVA-C02_orig_056", "E", False, "VPC エンドポイントにセキュリティグループをアタッチし、VPC の CIDR からのインバウンドのみを許可する。API のエンドポイントタイプは既定のままとする。"),
    # --- 057 Secrets Manager ローテーション直後 --------------------------
    ("DVA-C02_orig_057", "A", True, "アプリケーションで認証エラーを検知したときにシークレットのキャッシュを破棄して再取得する。必要に応じて AWSPREVIOUS ステージの値でも接続を試すロジックを実装する。"),
    ("DVA-C02_orig_057", "B", False, "アプリケーションで認証エラーを検知したときにシークレットのキャッシュを破棄して再取得する。必要に応じて AWSPENDING ステージの値でも接続を試すロジックを実装する。"),
    ("DVA-C02_orig_057", "C", False, "アプリケーションのシークレットのキャッシュの TTL を延長する。ローテーション後も取得済みの認証情報を長く使い続けられるようにする。"),
    ("DVA-C02_orig_057", "D", False, "シークレットを AWS Systems Manager パラメータストアの SecureString に移行する。アプリケーションは毎回パラメータストアから取得するよう変更する。"),
    # --- 074 (5肢/正解2) Step Functions Map ------------------------------
    ("DVA-C02_orig_074", "A", True, "Map ステートを使用して配列の各要素に対する処理を並列に実行する。MaxConcurrency で同時実行数を制御する。"),
    ("DVA-C02_orig_074", "B", True, "各処理ステップに Retry と Catch を定義する。再試行しても失敗した要素はエラー処理用のステートへ遷移させてワークフローを継続する。"),
    ("DVA-C02_orig_074", "C", False, "Parallel ステートを使用して、数千件のレコードに対する処理を同時に実行する。各ブランチで同じ Lambda 関数を呼び出す。"),
    ("DVA-C02_orig_074", "D", False, "Map ステートを使用して各要素を処理する。Wait ステートで各レコードの処理間隔を空ける。"),
    ("DVA-C02_orig_074", "E", False, "各処理ステップに Retry のみを定義する。指数バックオフで再試行を繰り返して、失敗した要素も成功するまで再実行し続ける。"),
    # --- 075 Firehose ----------------------------------------------------
    ("DVA-C02_orig_075", "A", True, "Amazon Data Firehose (Kinesis Data Firehose) の配信ストリームを作成する。送信先を S3 バケットに設定してバッファリングと圧縮を構成する。"),
    ("DVA-C02_orig_075", "B", False, "Amazon Kinesis Data Streams にログを送信する。Amazon EC2 上で稼働する自作のコンシューマーアプリケーションが S3 へ書き込む。"),
    ("DVA-C02_orig_075", "C", False, "アプリケーションがログレコードごとに Amazon S3 の PutObject API を呼び出して直接書き込む。バッファリングと圧縮の処理もアプリケーション側のコードとして実装する。"),
    ("DVA-C02_orig_075", "D", False, "Amazon SQS キューにログを送信する。AWS Lambda 関数がメッセージをバッファリングして圧縮したうえで S3 へ書き込む。"),
    # --- 092 Elastic Beanstalk CNAME スワップ ----------------------------
    ("DVA-C02_orig_092", "A", True, "既存環境をクローンして新しい環境を作成し、新バージョンをデプロイして検証する。その後、2 つの環境の URL (CNAME) をスワップする。"),
    ("DVA-C02_orig_092", "B", False, "既存環境に対して Immutable デプロイポリシーで新バージョンをデプロイする。新しいインスタンス群で検証してから切り替える。"),
    ("DVA-C02_orig_092", "C", False, "既存環境に対して新バージョンをデプロイする。デプロイポリシーは Rolling with additional batch を使用する。"),
    ("DVA-C02_orig_092", "D", False, "新しい Elastic Beanstalk 環境を作成する。RDS データベースを新環境に統合したうえでアプリケーションを切り替える。"),
    # --- 301 DecodeAuthorizationMessage ----------------------------------
    ("DVA-C02_orig_301", "A", True, "エンコードされたメッセージを AWS STS の DecodeAuthorizationMessage に渡してデコードする。出力から拒否の判断に使われたポリシーと条件キーの値を確認する。"),
    ("DVA-C02_orig_301", "B", False, "エンコードされたメッセージを Base64 デコードのコマンドでローカルに変換する。出力から拒否の判断に使われたポリシーと条件キーの値を確認する。"),
    ("DVA-C02_orig_301", "C", False, "IAM ポリシーシミュレーターで対象のロールと RunInstances アクションを選び、条件キーの値を入力してシミュレーションを実行する。結果から拒否の判断に使われたポリシーを確認する。"),
    ("DVA-C02_orig_301", "D", False, "AWS CloudTrail のイベント履歴で該当の RunInstances イベントを検索する。記録された errorMessage から拒否の理由を確認する。"),
]

out = []
for qid, L, ac, t in P:
    d = {"id": qid, "letter": L, "text": t}
    if ac:
        d["allow_correct"] = True
    out.append(d)
OUT = BASE / "資料" / "生成" / "_dva2s_patch.json"
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("patch: %d肢 / %d問  (正解肢 %d / 誤答肢 %d)" % (
    len(out), len({p["id"] for p in out}),
    sum(1 for x in P if x[2]), sum(1 for x in P if not x[2])))
