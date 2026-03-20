# CLAUDE-JP.md - loadtest-api-bench プロジェクト指示書

## プロジェクト概要

FastAPI で構築した負荷テスト用 API バックエンド。Locust を使い、Cloud Run 上で Cloud SQL / Spanner / BigQuery のレスポンス特性を比較する。

## 決定済み事項 (変更不可)

以下は検討済みで確定した方針。必ず従うこと:

1. **フレームワーク**: FastAPI
2. **ORM**: SQLAlchemy 2.0
3. **PK**: UUID (Spanner 互換のため全 DB で統一)
4. **クラス設計**: Template Method パターン (案C) — 詳細は `docs/ARCHITECTURE.md`
5. **async/sync**: async インターフェースで統一。Cloud SQL/SQLite は native async、Spanner/BigQuery は `asyncio.to_thread()` でラップ
6. **API 仕様**: api.yaml は仕様参照ドキュメントとして維持。サーバーコード生成 (openapi-generator) は使用せず、手書き実装を `src/loadtest_api/` に配置。api.yaml との整合性は schemathesis 契約テストで検証
7. **テスト**: TDD (t-wada 式 Red-Green-Refactor)。現時点は単体テストのみ (SQLite in-memory)。結合テストは後日追加
8. **DI**:
   - ログ: Cloud Run では構造化 JSON、ローカルでは人間向けフォーマット
   - DB: テスト時は SQLite、本番は実 DB
9. **DB 操作**: Read のみ (Write なし)
10. **シードデータ**: 約 10 万件
11. **リポジトリ**: `loadtest-api-bench` (GitHub public)

## プロジェクト構成

```
loadtest-api-bench/
├── api.yaml                    # OpenAPI 仕様 (Single Source of Truth)
├── pyproject.toml              # Rye プロジェクト設定
├── Dockerfile
├── deploy.sh                   # Cloud Run デプロイスクリプト
├── .env.example                # 環境変数テンプレート
├── .github/
│   └── workflows/
│       └── ci.yml              # CI パイプライン
├── output/                     # .gitignore で除外 (openapi-generator 出力、参照用)
├── scripts/
│   └── seed.py                 # シードデータ生成スクリプト
├── devlog/                     # 開発日誌
├── src/
│   └── loadtest_api/
│       ├── __init__.py
│       ├── main.py             # FastAPI アプリ
│       ├── config.py           # pydantic-settings
│       ├── dependencies.py     # DI プロバイダー
│       ├── logging.py          # ログ形式ファクトリ
│       ├── middleware.py        # リクエスト/レスポンス ミドルウェア
│       ├── models/
│       │   └── user.py         # SQLAlchemy ORM + Pydantic スキーマ
│       ├── api/
│       │   └── users.py        # ルートハンドラ
│       └── repositories/
│           ├── base.py         # DBAccessor (ABC)
│           ├── async_accessor.py  # AsyncDBAccessor
│           ├── sync_accessor.py   # SyncDBAccessor
│           ├── sqlite.py       # SQLiteAccessor
│           ├── cloud_sql.py    # CloudSQLAccessor
│           ├── spanner.py      # SpannerAccessor
│           └── bigquery.py     # BigQueryAccessor
├── tests/
│   ├── conftest.py             # SQLite in-memory fixture
│   ├── test_repositories.py    # Repository 単体テスト
│   ├── test_api_users.py       # API エンドポイントテスト
│   ├── test_middleware.py      # ミドルウェア単体テスト
│   ├── test_logging.py         # ログ単体テスト
│   └── test_seed.py            # シードスクリプト単体テスト
└── (Locust シナリオは別リポジトリで管理予定)
```

## 開発コマンド

```bash
rye run pytest tests/ -v        # テスト実行
rye run python scripts/seed.py --db-type sqlite --sqlite-path seed.db --count 100000  # シードデータ生成
uvicorn loadtest_api.main:app --reload  # ローカル開発サーバー起動
```

## 実装順序

1. Rye プロジェクト初期化 + api.yaml 作成
2. 手書き FastAPI 実装 (api.yaml を仕様参照、schemathesis で契約テスト)
3. DI 基盤構築 (config, logging, repository protocol)
4. TDD: SQLite Repository → API エンドポイント
5. Cloud SQL / Spanner / BigQuery Repository 追加
6. Dockerfile + Cloud Run 設定
7. Locustfile → **別リポジトリで管理予定**

## テストメソッド命名規約

日本語でシナリオ名を書く:
```python
def test_ユーザーIDで1件取得できる():
    ...
```

## アーキテクチャ詳細

クラス設計の詳細・コード例・採用理由は `docs/ARCHITECTURE.md` を参照。
