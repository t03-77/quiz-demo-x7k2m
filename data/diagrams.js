/* 解説画面に出す図（Mermaid記法）
 *
 * 問題ごとに図を作るとコストが高いので、頻出トピック単位で作って共有する。
 * match の語がすべて「問題文 + 正解の選択肢」に含まれたとき、その図を表示する。
 * 語の並び順は関係ない。exams を書くとその資格だけに絞れる。
 *
 * 図が見つからない問題では何も表示しない（「図なし」とは出さない）。
 */
window.DIAGRAMS = [
{
  id: 'vpc-endpoint',
  title: 'VPCエンドポイントの2種類',
  match: ['エンドポイント'],
  mermaid: `flowchart LR
  subgraph VPC
    E["EC2 / Lambda"]
    GW["ゲートウェイ型<br/>(ルートテーブルに経路)"]
    IF["インターフェイス型<br/>(ENI + プライベートIP)"]
  end
  E -->|"経路指定"| GW
  E -->|"DNS解決"| IF
  GW --> S3["Amazon S3"]
  GW --> DDB["Amazon DynamoDB"]
  IF --> OTHER["その他の多くのサービス<br/>(PrivateLink)"]
  note["ゲートウェイ型が使えるのは S3 と DynamoDB のみ。<br/>料金はかからないが、オンプレミスからは利用できない"]
  style note fill:#fff,stroke:#bbb,color:#555`,
},
{
  id: 's3-encryption',
  title: 'S3の暗号化方式と鍵の管理者',
  match: ['S3', '暗号化'],
  mermaid: `flowchart TB
  Q{"鍵を誰が管理するか"}
  Q -->|"AWSに任せる"| A["SSE-S3<br/>鍵の管理も操作記録もAWS側"]
  Q -->|"自分で管理したい"| B["SSE-KMS"]
  Q -->|"鍵を渡して都度指定"| C["SSE-C<br/>鍵はAWSに保存されない"]
  Q -->|"送る前に暗号化"| D["クライアントサイド暗号化"]
  B --> B1["AWSマネージドキー<br/>(aws/s3)<br/>キーポリシーは編集不可"]
  B --> B2["カスタマー管理キー<br/>キーポリシーを編集でき<br/>CloudTrailで復号を追跡できる"]
  style B2 fill:#e8f4ff,stroke:#6aa9e9`,
},
{
  id: 'dr-strategy',
  title: '災害復旧の4戦略（RTO/RPOとコスト）',
  match: ['RTO'],
  mermaid: `flowchart LR
  A["バックアップ&リストア<br/>RTO・RPO: 数時間〜<br/>コスト: 最小"]
  B["パイロットライト<br/>データは常時複製<br/>アプリ層は停止しておく"]
  C["ウォームスタンバイ<br/>縮小構成を常時稼働<br/>切替時に拡張"]
  D["マルチサイト<br/>アクティブ/アクティブ<br/>RTO・RPO: ほぼゼロ<br/>コスト: 最大"]
  A --> B --> C --> D
  style A fill:#f6f6f6,stroke:#bbb
  style D fill:#ffeaea,stroke:#e98b8b`,
},
{
  id: 'iam-evaluation',
  title: 'IAMの権限評価の流れ',
  match: ['SCP'],
  mermaid: `flowchart TB
  S["リクエスト"] --> D1{"明示的な拒否が<br/>どこかにあるか"}
  D1 -->|"ある"| NG["拒否"]
  D1 -->|"ない"| D2{"SCPで許可されているか"}
  D2 -->|"されていない"| NG
  D2 -->|"されている"| D3{"アクセス許可の境界の<br/>範囲内か"}
  D3 -->|"範囲外"| NG
  D3 -->|"範囲内"| D4{"アイデンティティベース<br/>またはリソースベースの<br/>ポリシーで許可されているか"}
  D4 -->|"許可なし"| NG
  D4 -->|"許可あり"| OK["許可"]
  style NG fill:#ffeaea,stroke:#e98b8b
  style OK fill:#eaf7ea,stroke:#8bc98b`,
},
{
  id: 'sqs-sns-eb',
  title: 'SQS / SNS / EventBridge の使い分け',
  match: ['SQS'],
  mermaid: `flowchart LR
  P["送信側"] --> SQS["Amazon SQS<br/>1対1のキュー<br/>受信側が自分のペースで取り出す<br/>処理の平準化・疎結合"]
  P --> SNS["Amazon SNS<br/>1対多の配信<br/>購読者全員に同時に届く"]
  P --> EB["Amazon EventBridge<br/>内容でルーティング<br/>SaaS連携・スケジュール実行"]
  SQS --> W1["ワーカー"]
  SNS --> Q1["SQSキュー"]
  SNS --> L1["Lambda"]
  EB --> T1["多数のターゲット"]`,
},
{
  id: 'cloudfront-oac',
  title: 'CloudFront + OAC でS3を保護する経路',
  match: ['CloudFront', 'S3'],
  mermaid: `flowchart LR
  U["利用者"] --> CF["CloudFront<br/>エッジロケーション"]
  CF -->|"署名付きリクエスト<br/>(OAC)"| S3["S3バケット<br/>パブリックアクセスは全てブロック"]
  U -.->|"直接アクセスは拒否される"| S3
  CF --- W["AWS WAF<br/>(ディストリビューションに関連付け)"]
  style W fill:#f6f6f6,stroke:#bbb`,
},
{
  id: 'rds-ha',
  title: 'RDSのマルチAZとリードレプリカ（目的が違う）',
  match: ['リードレプリカ'],
  mermaid: `flowchart TB
  subgraph HA["マルチAZ配置 — 可用性のため"]
    P1["プライマリ<br/>AZ-a"] -->|"同期レプリケーション"| S1["スタンバイ<br/>AZ-b<br/>読み取りには使えない"]
    P1 -.->|"障害時に自動フェイルオーバー<br/>エンドポイントは変わらない"| S1
  end
  subgraph RR["リードレプリカ — 読み取り性能のため"]
    P2["プライマリ"] -->|"非同期レプリケーション"| R1["レプリカ1<br/>読み取り可"]
    P2 --> R2["レプリカ2<br/>別リージョンにも作れる"]
  end`,
},
{
  id: 'cicd-pipeline',
  title: 'CodePipeline の基本構成',
  match: ['CodePipeline'],
  mermaid: `flowchart LR
  SRC["ソース<br/>GitHub / S3<br/>CodeConnectionsで接続"] --> BLD["ビルド<br/>CodeBuild<br/>buildspec.yml"]
  BLD --> APV["承認<br/>(手動承認アクション)"]
  APV --> DEP["デプロイ<br/>CodeDeploy / CFn / ECS"]
  DEP --> PRD["本番環境"]
  BLD -.->|"成果物"| ART["アーティファクトストア<br/>(S3)"]
  ART -.-> DEP`,
},
{
  id: 'asg-lifecycle',
  title: 'Auto Scaling のライフサイクルフック',
  match: ['ライフサイクルフック'],
  mermaid: `flowchart LR
  A["スケールアウト開始"] --> B["Pending"]
  B --> H1["Pending:Wait<br/>(起動時フック)<br/>初期化処理を実行"]
  H1 --> C["InService"]
  C --> D["Terminating"]
  D --> H2["Terminating:Wait<br/>(終了時フック)<br/>ログの退避・接続の切り離し"]
  H2 --> E["Terminated"]
  style H1 fill:#e8f4ff,stroke:#6aa9e9
  style H2 fill:#e8f4ff,stroke:#6aa9e9`,
},
{
  id: 'lambda-invoke',
  title: 'Lambda の3つの呼び出し方と失敗時の挙動',
  match: ['Lambda', '再試行'],
  mermaid: `flowchart TB
  S["同期呼び出し<br/>API Gateway など"] --> S1["呼び出し元に結果を返す<br/>再試行は呼び出し元の責任"]
  A["非同期呼び出し<br/>S3イベント / SNS"] --> A1["Lambdaが自動で2回再試行<br/>失敗分はDLQ / 送信先へ"]
  P["ストリーム/キュー<br/>Kinesis / DynamoDB / SQS"] --> P1["Lambdaがポーリング<br/>バッチ単位で処理<br/>成功するまでブロックしうる"]
  style A1 fill:#e8f4ff,stroke:#6aa9e9`,
},
{
  id: 'kinesis-shard',
  title: 'Kinesis Data Streams のシャードと順序',
  match: ['シャード'],
  mermaid: `flowchart LR
  P["プロデューサー"] -->|"パーティションキー"| SH1["シャード1<br/>この中では順序が保たれる"]
  P --> SH2["シャード2"]
  P --> SH3["シャード3"]
  SH1 --> C1["コンシューマー"]
  SH2 --> C1
  SH3 --> C1
  note["スループットを上げるにはシャードを増やす。<br/>同じパーティションキーは常に同じシャードへ入るため、<br/>キーが偏るとホットシャードになる"]
  style note fill:#fff,stroke:#bbb,color:#555`,
},
{
  id: 'org-scp',
  title: 'Organizations の階層とSCPの効き方',
  match: ['Organizations'],
  mermaid: `flowchart TB
  R["ルート"] --> OU1["OU: 本番"]
  R --> OU2["OU: 開発"]
  OU1 --> A1["アカウントA"]
  OU1 --> A2["アカウントB"]
  OU2 --> A3["アカウントC"]
  R -.->|"SCPは上位から継承され<br/>重なった範囲だけが許可される"| OU1
  MGMT["管理アカウント<br/>SCPの影響を受けない"]
  style MGMT fill:#fff4e5,stroke:#e9b96a`,
},
{
  id: 'ecs-launch',
  title: 'ECS の起動タイプ（Fargate と EC2）',
  match: ['ECS'],
  mermaid: `flowchart TB
  T["タスク定義"] --> Q{"実行基盤を<br/>誰が管理するか"}
  Q -->|"AWSに任せる"| F["Fargate<br/>サーバー管理が不要<br/>タスク単位の課金<br/>Spotも選べる"]
  Q -->|"自分で持つ"| E["EC2起動タイプ<br/>インスタンスの選択・パッチ適用は自分<br/>1台に複数タスクを詰められる<br/>GPUなど特殊要件に対応"]
  F --> CP["キャパシティープロバイダー<br/>FARGATE と FARGATE_SPOT を<br/>base / weight で配分"]
  style CP fill:#e8f4ff,stroke:#6aa9e9`,
},
{
  id: 'bedrock-rag',
  title: 'Bedrock Knowledge Bases によるRAGの流れ',
  match: ['Knowledge Bases'],
  exams: ['AIP-C01', 'AIF-C01', 'MLA-C01'],
  mermaid: `flowchart LR
  S3["S3のソース文書"] -->|"取り込み・分割"| CH["チャンク化"]
  CH -->|"埋め込みモデル"| VEC["ベクトル化"]
  VEC --> DB["ベクトルストア<br/>OpenSearch Serverless<br/>Aurora PostgreSQL など"]
  U["利用者の質問"] --> VEC2["質問をベクトル化"]
  VEC2 --> DB
  DB -->|"関連チャンクを取得"| FM["基盤モデル"]
  FM --> ANS["根拠付きの回答"]`,
},
];
