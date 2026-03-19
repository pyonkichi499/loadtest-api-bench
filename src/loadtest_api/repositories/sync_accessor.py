import asyncio
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from loadtest_api.repositories.base import DBAccessor


class SyncDBAccessor(DBAccessor):
    def __init__(self, engine: Engine) -> None:
        self._session_factory = sessionmaker(engine, expire_on_commit=False)

    def _sync_scalar_one_or_none(self, stmt: Any) -> Any:
        with self._session_factory() as s:
            return s.execute(stmt).scalar_one_or_none()

    def _sync_scalars_all(self, stmt: Any) -> list[Any]:
        with self._session_factory() as s:
            return list(s.execute(stmt).scalars().all())

    def _sync_one(self, stmt: Any) -> Any:
        with self._session_factory() as s:
            return s.execute(stmt).one()

    async def _scalar_one_or_none(self, stmt: Any) -> Any:
        return await asyncio.to_thread(self._sync_scalar_one_or_none, stmt)

    async def _scalars_all(self, stmt: Any) -> list[Any]:
        return await asyncio.to_thread(self._sync_scalars_all, stmt)

    async def _one(self, stmt: Any) -> Any:
        return await asyncio.to_thread(self._sync_one, stmt)
