from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import func, select

from loadtest_api.models.user import StatsSchema, User, UserSchema


class DBAccessor(ABC):
    @staticmethod
    def _escape_like(value: str) -> str:
        """LIKE ワイルドカード文字（%, _）をバックスラッシュでエスケープする。"""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def get_user_by_id(self, user_id: str) -> UserSchema | None:
        stmt = select(User).where(User.id == user_id)
        row = await self._scalar_one_or_none(stmt)
        return UserSchema.model_validate(row) if row else None

    async def list_users(self, limit: int = 100) -> list[UserSchema]:
        stmt = select(User).limit(limit)
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]

    async def search_users(self, name: str) -> list[UserSchema]:
        escaped = self._escape_like(name)
        stmt = select(User).where(User.name.ilike(f"%{escaped}%", escape="\\"))
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]

    async def get_stats(self) -> StatsSchema:
        stmt = select(func.count(), func.avg(User.age)).select_from(User)
        row = await self._one(stmt)
        return StatsSchema(count=row[0], avg_age=float(row[1]) if row[1] is not None else None)

    @abstractmethod
    async def _scalar_one_or_none(self, stmt: Any) -> Any: ...

    @abstractmethod
    async def _scalars_all(self, stmt: Any) -> list[Any]: ...

    @abstractmethod
    async def _one(self, stmt: Any) -> Any: ...
