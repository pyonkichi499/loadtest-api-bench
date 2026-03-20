"""api.yaml と FastAPI 実装の整合性を検証する契約テスト.

schemathesis を使い、api.yaml に定義された全エンドポイントに対して
自動生成リクエストを送信し、レスポンスが OpenAPI 仕様に準拠しているかを確認する。
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import schemathesis
from hypothesis import strategies as st
from schemathesis import Case, HookContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from loadtest_api.dependencies import get_db_accessor
from loadtest_api.main import app
from loadtest_api.models.user import Base, User
from loadtest_api.repositories.async_accessor import AsyncDBAccessor
from loadtest_api.repositories.base import DBAccessor

# --- シードデータの user_id（hook でパスパラメータに注入するため） ---
SEED_USER_IDS: list[str] = [
    str(uuid.uuid4()),
    str(uuid.uuid4()),
    str(uuid.uuid4()),
]


def _setup_db_and_override() -> DBAccessor:
    """SQLite in-memory に DB を作成し、シードデータを投入し、DI をオーバーライドする."""
    loop = asyncio.new_event_loop()
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async def _init() -> AsyncDBAccessor:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            users = [
                User(id=SEED_USER_IDS[0], name="Alice Smith", age=30, email="alice@example.com"),
                User(id=SEED_USER_IDS[1], name="Bob Johnson", age=25, email="bob@example.com"),
                User(id=SEED_USER_IDS[2], name="Charlie Brown", age=35, email="charlie@example.com"),
            ]
            session.add_all(users)
            await session.commit()
        return AsyncDBAccessor(engine)

    accessor = loop.run_until_complete(_init())
    loop.close()
    app.dependency_overrides[get_db_accessor] = lambda: accessor
    return accessor


# --- DB セットアップを実行し DI をオーバーライド ---
_setup_db_and_override()

# --- schemathesis スキーマを api.yaml から読み込み ---
schema = schemathesis.openapi.from_path(
    "api.yaml",
)
schema.app = app


# --- /users/{user_id} に対して既知の UUID を注入する hook ---
@schema.hook("before_generate_path_parameters")
def inject_known_user_id(
    context: HookContext,
    strategy: st.SearchStrategy[dict[str, Any]],
) -> st.SearchStrategy[dict[str, Any]]:
    """user_id パスパラメータにシードデータの UUID を注入する.

    /users/{user_id} エンドポイントでは存在する UUID を使わないと 404 になり、
    schemathesis が正常なレスポンス検証を行えないため。
    """
    if context.operation is not None and "user_id" in (context.operation.path or ""):
        return st.sampled_from(SEED_USER_IDS).map(lambda uid: {"user_id": uid})
    return strategy


# --- 契約テスト ---
@schema.parametrize()
def test_OpenAPI仕様とAPIレスポンスの整合性を検証する(case: Case) -> None:
    """api.yaml の全エンドポイントに対してリクエストを生成し、レスポンスが仕様に準拠しているか確認する."""
    response = case.call()
    case.validate_response(response)
