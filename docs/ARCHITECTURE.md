# Architecture

## クラス設計: Template Method パターン (案C)

### 設計思想

「何をクエリするか (SQL 組み立て)」と「どう実行するか (async/sync)」を分離する。

### クラス階層

```
DBAccessor (基底: SQL 組み立て + ビジネスロジック)
├── AsyncDBAccessor (中間: async engine で実行)
│   ├── CloudSQLAccessor  ... engine 設定のみ (postgresql+asyncpg)
│   └── SQLiteAccessor    ... engine 設定のみ (sqlite+aiosqlite)
└── SyncDBAccessor (中間: sync → asyncio.to_thread でラップ)
    ├── SpannerAccessor   ... engine 設定のみ (sqlalchemy-spanner)
    └── BigQueryAccessor  ... engine 設定のみ (sqlalchemy-bigquery)
```

### 採用理由

3 案を検討し、案C を採用した。

| | 案A: sync 統一 | 案B: async 基底 + 全メソッド override | **案C: Template Method** |
|---|---|---|---|
| クエリロジックの重複 | なし | 全メソッド × 子クラス数 | **なし** |
| 子クラスの override 量 | engine のみ | 全メソッド | **execute 系の 3 メソッドのみ** |
| async 対応 | なし | あり | **あり** |
| DB 固有 SQL 対応 | - | 子クラスでメソッド丸ごと override | **必要な場合だけ基底メソッドを override** |

### 各層の責務

#### DBAccessor (基底クラス)

- SQLAlchemy の `select()` 等でクエリを組み立てる
- Pydantic モデルへの変換を行う
- 子クラスに `_scalar_one_or_none()`, `_scalars_all()`, `_one()` の実装を要求する

```python
class DBAccessor(ABC):
    async def get_user_by_id(self, user_id: str) -> UserSchema | None:
        stmt = select(User).where(User.id == user_id)
        row = await self._scalar_one_or_none(stmt)
        return UserSchema.model_validate(row) if row else None

    async def list_users(self, limit: int = 100) -> list[UserSchema]:
        stmt = select(User).limit(limit)
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]

    async def search_users(self, name: str) -> list[UserSchema]:
        stmt = select(User).where(User.name.ilike(f"%{name}%"))
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]

    async def get_stats(self) -> StatsSchema:
        stmt = select(func.count(), func.avg(User.age)).select_from(User)
        row = await self._one(stmt)
        return StatsSchema(count=row[0], avg_age=row[1])

    @abstractmethod
    async def _scalar_one_or_none(self, stmt) -> Any: ...
    @abstractmethod
    async def _scalars_all(self, stmt) -> list[Any]: ...
    @abstractmethod
    async def _one(self, stmt) -> Any: ...
```

#### AsyncDBAccessor (中間クラス: Cloud SQL / SQLite 用)

```python
class AsyncDBAccessor(DBAccessor):
    def __init__(self, async_engine: AsyncEngine):
        self.async_session = async_sessionmaker(async_engine)

    async def _scalar_one_or_none(self, stmt):
        async with self.async_session() as s:
            return (await s.execute(stmt)).scalar_one_or_none()

    async def _scalars_all(self, stmt):
        async with self.async_session() as s:
            return (await s.execute(stmt)).scalars().all()

    async def _one(self, stmt):
        async with self.async_session() as s:
            return (await s.execute(stmt)).one()
```

#### SyncDBAccessor (中間クラス: Spanner / BigQuery 用)

Spanner / BigQuery の Python クライアントは async 非対応のため、`asyncio.to_thread` で sync 呼び出しをラップする。

```python
class SyncDBAccessor(DBAccessor):
    def __init__(self, engine: Engine):
        self.SessionFactory = sessionmaker(engine)

    async def _scalar_one_or_none(self, stmt):
        return await asyncio.to_thread(self._sync_scalar_one_or_none, stmt)

    def _sync_scalar_one_or_none(self, stmt):
        with self.SessionFactory() as s:
            return s.execute(stmt).scalar_one_or_none()

    # _scalars_all, _one も同様のパターン
```

#### 末端クラス (各 DB 固有: 接続設定のみ)

```python
class CloudSQLAccessor(AsyncDBAccessor):
    def __init__(self, dsn: str, pool_size: int = 5, max_overflow: int = 10):
        engine = create_async_engine(dsn, pool_size=pool_size, max_overflow=max_overflow)
        super().__init__(engine)

class SQLiteAccessor(AsyncDBAccessor):
    def __init__(self, path: str = ":memory:"):
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}", echo=False)
        super().__init__(engine)

class SpannerAccessor(SyncDBAccessor):
    def __init__(self, project: str, instance: str, database: str):
        url = f"spanner:///projects/{project}/instances/{instance}/databases/{database}"
        engine = create_engine(url)
        super().__init__(engine)

class BigQueryAccessor(SyncDBAccessor):
    def __init__(self, project: str, dataset: str):
        engine = create_engine(f"bigquery://{project}/{dataset}")
        super().__init__(engine)
```

### DB 固有の差異と吸収方法

| 差異 | 影響 | 対処 |
|---|---|---|
| Spanner は auto-increment 不可 | PK 生成方式 | UUID に統一済み (全 DB 共通) |
| Spanner は `ILIKE` 未対応 | `search_users` のクエリ | SpannerAccessor で `search_users` を override |
| BigQuery は集計が得意だがレイテンシ高い | `get_stats` の挙動 | override 不要 (同じ SQL で動くが遅い) |
| コネクションプール設定 | engine 生成時 | 各末端クラスのコンストラクタで吸収 |

Spanner の `ILIKE` 問題の対処例:

```python
class SpannerAccessor(SyncDBAccessor):
    async def search_users(self, name: str) -> list[UserSchema]:
        stmt = select(User).where(func.lower(User.name).like(f"%{name.lower()}%"))
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]
```

## async / sync の設計

### SQLAlchemy dialect の async 対応状況

| DB | dialect | async 対応 |
|---|---|---|
| SQLite | `sqlite+aiosqlite` | あり |
| Cloud SQL (PostgreSQL) | `postgresql+asyncpg` | あり |
| Spanner | `sqlalchemy-spanner` | なし (sync only) |
| BigQuery | `sqlalchemy-bigquery` | なし (sync only) |

### 方針

- DBAccessor のインターフェースは **async で統一**
- Cloud SQL / SQLite は native async (asyncpg / aiosqlite)
- Spanner / BigQuery は `asyncio.to_thread()` で sync を async にラップ
- FastAPI 側は全て `async def` で統一

### async vs sync の負荷テストでの意味

- **sync**: DB の応答を待っている間、他のリクエストを処理できない
- **async**: DB の応答を待っている間、他のリクエストを並行処理できる
- Cloud Run のスケーリング挙動に影響: async の方が 1 インスタンスあたりの処理能力が高い

## Dependency Injection (DI)

FastAPI の `Depends()` を使って以下を切り替える。

### 3-a. ログ形式の切り替え

| 環境 | フォーマット | 出力先 |
|---|---|---|
| ローカル | 人間が読みやすい形式 (色付き) | stderr |
| テスト | 最小限 or 無効 | - |
| Cloud Run | 構造化 JSON | stdout → Cloud Logging が自動収集 |

### 3-b. DB の切り替え

| 環境 | DB |
|---|---|
| 単体テスト | SQLite (in-memory) |
| ローカル開発 | SQLite or Cloud SQL |
| Cloud Run | Cloud SQL / Spanner / BigQuery |

```python
def get_db_accessor(settings: Settings = Depends(get_settings)) -> DBAccessor:
    match settings.db_type:
        case "sqlite":
            return SQLiteAccessor()
        case "cloud_sql":
            return CloudSQLAccessor(dsn=settings.cloud_sql_dsn)
        case "spanner":
            return SpannerAccessor(...)
        case "bigquery":
            return BigQueryAccessor(...)
```

## openapi-generator 運用方針

**api.yaml を Single Source of Truth** とする運用を採用。

- `api.yaml` を変更するたびに openapi-generator で再生成する
- 生成コードは `output/` ディレクトリに出力 (再生成で上書きされる)
- 手書きコードは `src/loadtest_api/` に配置 (`output/` を import して使う)
- 生成コードとカスタムコードを厳密に分離する

## テスト戦略

t-wada 式 TDD (Red-Green-Refactor) に従う。

### スコープ (現時点)

単体テストのみ。結合テストは実 DB 準備後に追加。

### 単体テストケース一覧

**Repository 層:**

| テストケース | 検証内容 |
|---|---|
| `test_ユーザーIDで1件取得できる` | PK lookup が正しく動く |
| `test_存在しないIDはNoneを返す` | 該当なしの場合の挙動 |
| `test_一覧取得でlimitが効く` | limit=10 で 10 件だけ返る |
| `test_limit未指定でデフォルト100件` | デフォルト値の確認 |
| `test_名前で部分一致検索できる` | ILIKE 相当の動作 |
| `test_検索結果0件は空リストを返す` | 該当なしの場合 |
| `test_統計情報でcountとavg_ageが返る` | 集計クエリの動作 |
| `test_データ0件の統計情報` | 空テーブルでの集計 |

**API 層:**

| テストケース | 検証内容 |
|---|---|
| `test_GET_users_idで200が返る` | 正常系レスポンス |
| `test_存在しないIDで404が返る` | エラーレスポンス |
| `test_GET_usersでリスト取得できる` | 一覧の正常系 |
| `test_limitにマイナス値で422が返る` | バリデーション |
| `test_GET_users_searchで検索できる` | 検索の正常系 |
| `test_GET_users_statsで統計取得できる` | 集計の正常系 |
| `test_healthチェックで200が返る` | ヘルスチェック |

### テスト実行

```bash
rye run pytest tests/ -v
```

### テスト用 fixture

- SQLite in-memory を使用
- `conftest.py` で DBAccessor の DI を override
- `httpx.AsyncClient` + `ASGITransport` で FastAPI を直接テスト
