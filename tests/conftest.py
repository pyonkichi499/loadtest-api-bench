import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from loadtest_api.models.user import Base, User
from loadtest_api.repositories.async_accessor import AsyncDBAccessor
from loadtest_api.repositories.base import DBAccessor


# --- テストデータ定義 ---

SEED_USERS: list[dict[str, str | int]] = [
    {"name": "Alice Smith", "age": 30, "email": "alice@example.com"},
    {"name": "Bob Johnson", "age": 25, "email": "bob@example.com"},
    {"name": "Charlie Alice Brown", "age": 35, "email": "charlie@example.com"},
]


# --- エンジンヘルパー ---


async def _create_test_engine() -> AsyncEngine:
    """テスト用 SQLite in-memory エンジンを作成しテーブルを初期化する。"""
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def _cleanup_engine(engine: AsyncEngine) -> None:
    """テスト用エンジンのテーブル削除と破棄を行う。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _seed_users(
    engine: AsyncEngine,
    users_data: list[dict[str, str | int]],
    ids: list[str] | None = None,
) -> list[str]:
    """テスト用ユーザーデータを投入し、使用した ID のリストを返す。"""
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in users_data]
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )
    async with session_factory() as session:
        users: list[User] = [
            User(id=ids[i], **data)  # type: ignore[arg-type]
            for i, data in enumerate(users_data)
        ]
        session.add_all(users)
        await session.commit()
    return ids


# --- Fixtures ---


@pytest.fixture
async def db_accessor() -> AsyncGenerator[DBAccessor, None]:
    engine: AsyncEngine = await _create_test_engine()
    await _seed_users(engine, SEED_USERS)
    accessor: DBAccessor = AsyncDBAccessor(engine)
    yield accessor
    await _cleanup_engine(engine)


@pytest.fixture
async def empty_db_accessor() -> AsyncGenerator[DBAccessor, None]:
    engine: AsyncEngine = await _create_test_engine()
    accessor: DBAccessor = AsyncDBAccessor(engine)
    yield accessor
    await _cleanup_engine(engine)


@pytest.fixture
async def seeded_accessor_with_ids() -> AsyncGenerator[tuple[DBAccessor, list[str]], None]:
    engine: AsyncEngine = await _create_test_engine()
    ids: list[str] = await _seed_users(engine, SEED_USERS)
    accessor: DBAccessor = AsyncDBAccessor(engine)
    yield accessor, ids
    await _cleanup_engine(engine)


@pytest.fixture
async def single_record_accessor() -> AsyncGenerator[tuple[DBAccessor, str], None]:
    engine: AsyncEngine = await _create_test_engine()
    single_user_data: list[dict[str, str | int]] = [
        {"name": "Only User", "age": 42, "email": "only@example.com"},
    ]
    ids: list[str] = await _seed_users(engine, single_user_data)
    accessor: DBAccessor = AsyncDBAccessor(engine)
    yield accessor, ids[0]
    await _cleanup_engine(engine)


@pytest.fixture
async def wildcard_db_accessor() -> AsyncGenerator[DBAccessor, None]:
    engine: AsyncEngine = await _create_test_engine()
    wildcard_users: list[dict[str, str | int]] = [
        {"name": "Alice Smith", "age": 30, "email": "alice@example.com"},
        {"name": "100% Juice", "age": 25, "email": "juice@example.com"},
        {"name": "Bob Johnson", "age": 28, "email": "bob@example.com"},
        {"name": "user_name_test", "age": 22, "email": "under@example.com"},
        {"name": "Normal User", "age": 35, "email": "normal@example.com"},
    ]
    await _seed_users(engine, wildcard_users)
    accessor: DBAccessor = AsyncDBAccessor(engine)
    yield accessor
    await _cleanup_engine(engine)


@pytest.fixture
async def async_client(
    seeded_accessor_with_ids: tuple[DBAccessor, list[str]],
) -> AsyncGenerator[tuple[AsyncClient, list[str]], None]:
    accessor, ids = seeded_accessor_with_ids
    from loadtest_api.dependencies import get_db_accessor
    from loadtest_api.main import app

    app.dependency_overrides[get_db_accessor] = lambda: accessor
    transport: ASGITransport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ids
    app.dependency_overrides.clear()
