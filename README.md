# loadtest-api-bench

Locust を使った負荷テスト用 FastAPI バックエンド。Cloud Run 上で Cloud SQL / Spanner / BigQuery のレスポンス特性を比較する。

## 目的

1. **Locust の習熟**: ユーザーシナリオ定義、段階的負荷増加、リアルタイム可視化、分散実行
2. **Cloud Run のスケーリング特性の理解**: concurrency / min・max instances / CPU allocation の挙動
3. **DB ごとのレスポンス特性の比較**: 同一負荷パターンで OLTP (Cloud SQL) / スケーラブル RDBMS (Spanner) / OLAP (BigQuery) を比較

## 技術スタック

| 要素 | 選定 | 理由 |
|---|---|---|
| API フレームワーク | **FastAPI** | async/sync 両対応、Depends() による DI、Cloud Run 事例豊富 |
| ORM / DB 抽象化 | **SQLAlchemy 2.0** | 全対象 DB に dialect あり。ORM モデル共通化が可能 |
| DB (OLTP) | **Cloud SQL (PostgreSQL)** | 実務で最も一般的な構成。コネクション枯渇の観察 |
| DB (スケーラブル) | **Spanner** (optional, 最小構成 100PU) | プロビジョニング課金 (読み書き無課金)。Cloud SQL との対比 |
| DB (OLAP) | **BigQuery** | OLTP 的負荷を掛けた時の崩壊パターンの観察 |
| テスト用 DB | **SQLite** (in-memory) | 単体テスト用。SQLAlchemy dialect で透過的に切替 |
| 負荷テスト | **Locust** | Python ベース、シナリオをコードで定義 |
| デプロイ先 | **Cloud Run** | コンテナ単位のオートスケール |
| プロジェクト管理 | **Rye** | Python プロジェクト管理 |
| コード生成 | **openapi-generator** | api.yaml → FastAPI コード生成 |

## API エンドポイント

全エンドポイントは **Read のみ** (Write なし)。

| エンドポイント | クエリ特性 | 観察ポイント |
|---|---|---|
| `GET /health` | 即時レスポンス | ベースライン測定 |
| `GET /users/{id}` | PK (UUID) 指定の 1 件取得 | 最速パターン |
| `GET /users?limit=N` | 一覧取得 (LIMIT) | レスポンスサイズの影響 |
| `GET /users/search?name=X` | インデックスなしカラムの検索 | full scan の負荷 |
| `GET /users/stats` | 集計 (COUNT, AVG) | 重いクエリの影響 |

各エンドポイントは 3 つの DB (Cloud SQL / Spanner / BigQuery) に対応するバリアントを持つ。

## DB ごとの 100 RPS 対応力

| DB | 100 RPS | 備考 |
|---|---|---|
| Cloud SQL (db-f1-micro) | ギリギリ〜厳しい | コネクション枯渇を観察できる |
| Spanner (100 PU) | 余裕 | 設計上 数千〜数万 RPS 想定 |
| BigQuery | 無理 | OLAP エンジン。1 クエリ数秒。崩壊パターンの観察が目的 |

## データ設計

- **PK**: UUID (Spanner が auto-increment 非対応のため全 DB で統一)
- **シードデータ**: 約 10 万件 (index scan と full scan の差が出るバランス)
- **テーブル**: users (id, name, age, email)
