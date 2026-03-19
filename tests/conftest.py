import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from loadtest_api.models.user import Base, User
from loadtest_api.repositories.async_accessor import AsyncDBAccessor
from loadtest_api.repositories.base import DBAccessor


@pytest.fixture
async def db_accessor() -> AsyncGenerator[DBAccessor, None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    accessor = AsyncDBAccessor(engine)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        users = [
            User(id=str(uuid.uuid4()), name="Alice Smith", age=30, email="alice@example.com"),
            User(id=str(uuid.uuid4()), name="Bob Johnson", age=25, email="bob@example.com"),
            User(id=str(uuid.uuid4()), name="Charlie Alice Brown", age=35, email="charlie@example.com"),
        ]
        session.add_all(users)
        await session.commit()

    yield accessor

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def empty_db_accessor() -> AsyncGenerator[DBAccessor, None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    accessor = AsyncDBAccessor(engine)
    yield accessor

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def seeded_accessor_with_ids() -> AsyncGenerator[tuple[DBAccessor, list[str]], None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    accessor = AsyncDBAccessor(engine)

    ids = [str(uuid.uuid4()) for _ in range(3)]
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        users = [
            User(id=ids[0], name="Alice Smith", age=30, email="alice@example.com"),
            User(id=ids[1], name="Bob Johnson", age=25, email="bob@example.com"),
            User(id=ids[2], name="Charlie Alice Brown", age=35, email="charlie@example.com"),
        ]
        session.add_all(users)
        await session.commit()

    yield accessor, ids

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def single_record_accessor() -> AsyncGenerator[tuple[DBAccessor, str], None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    accessor = AsyncDBAccessor(engine)

    user_id = str(uuid.uuid4())
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(User(id=user_id, name="Only User", age=42, email="only@example.com"))
        await session.commit()

    yield accessor, user_id

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_client(seeded_accessor_with_ids: tuple[DBAccessor, list[str]]) -> AsyncGenerator[tuple[AsyncClient, list[str]], None]:
    accessor, ids = seeded_accessor_with_ids
    from loadtest_api.dependencies import get_db_accessor
    from loadtest_api.main import app

    app.dependency_overrides[get_db_accessor] = lambda: accessor
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ids
    app.dependency_overrides.clear()
