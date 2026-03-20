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

## クイックスタート

### 前提条件

- Python 3.12+
- [Rye](https://rye.astral.sh/)

### セットアップ

```bash
git clone https://github.com/<your-org>/loadtest-api-bench.git
cd loadtest-api-bench
rye sync
```

### テスト実行

```bash
rye run pytest tests/ -v
```

### ローカル起動

```bash
rye run uvicorn loadtest_api.main:app --reload
```

ブラウザで http://localhost:8000/docs にアクセスすると Swagger UI が表示されます。

## 環境変数

すべての環境変数には `APP_` プレフィックスを付けて設定します（例: `APP_DB_TYPE=sqlite`）。

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `APP_DB_TYPE` | `sqlite` | 使用する DB (`sqlite` / `cloud_sql` / `spanner` / `bigquery`) |
| `APP_SQLITE_PATH` | `:memory:` | SQLite のファイルパス (`:memory:` でインメモリ) |
| `APP_CLOUD_SQL_DSN` | `""` | Cloud SQL (PostgreSQL) の接続文字列 |
| `APP_SPANNER_PROJECT` | `""` | Spanner の GCP プロジェクト ID |
| `APP_SPANNER_INSTANCE` | `""` | Spanner のインスタンス ID |
| `APP_SPANNER_DATABASE` | `""` | Spanner のデータベース名 |
| `APP_BIGQUERY_PROJECT` | `""` | BigQuery の GCP プロジェクト ID |
| `APP_BIGQUERY_DATASET` | `""` | BigQuery のデータセット名 |
| `APP_POOL_SIZE` | `5` | コネクションプールの常時接続数 (Cloud SQL 用) |
| `APP_MAX_OVERFLOW` | `10` | プール上限を超えて追加作成できる接続数 (Cloud SQL 用) |
| `APP_POOL_TIMEOUT` | `30` | プールから接続取得時のタイムアウト秒数 (Cloud SQL 用) |
| `APP_LOG_FORMAT` | `text` | ログ形式 (`text`: 人間向け / `json`: Cloud Run 向け構造化ログ) |

## プロジェクト構成

```
src/loadtest_api/
├── main.py                 # FastAPI アプリケーション
├── config.py               # pydantic-settings による設定管理
├── dependencies.py         # DI プロバイダ
├── logging.py              # ログフォーマット切替
├── api/
│   └── users.py            # ルートハンドラ
├── models/
│   └── user.py             # SQLAlchemy ORM + Pydantic スキーマ
└── repositories/
    ├── base.py             # DBAccessor (ABC)
    ├── async_accessor.py   # AsyncDBAccessor
    ├── sync_accessor.py    # SyncDBAccessor
    ├── sqlite.py           # SQLiteAccessor
    ├── cloud_sql.py        # CloudSQLAccessor
    ├── spanner.py          # SpannerAccessor
    └── bigquery.py         # BigQueryAccessor
```
