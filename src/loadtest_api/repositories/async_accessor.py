from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from loadtest_api.repositories.base import DBAccessor


class AsyncDBAccessor(DBAccessor):
    def __init__(self, async_engine: AsyncEngine) -> None:
        self.async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    async def _scalar_one_or_none(self, stmt: Any) -> Any:
        async with self.async_session() as s:
            return (await s.execute(stmt)).scalar_one_or_none()

    async def _scalars_all(self, stmt: Any) -> list[Any]:
        async with self.async_session() as s:
            return list((await s.execute(stmt)).scalars().all())

    async def _one(self, stmt: Any) -> Any:
        async with self.async_session() as s:
            return (await s.execute(stmt)).one()
