from sqlalchemy import create_engine, func, select

from loadtest_api.models.user import User, UserSchema
from loadtest_api.repositories.sync_accessor import SyncDBAccessor


class SpannerAccessor(SyncDBAccessor):
    def __init__(self, project: str, instance: str, database: str) -> None:
        url = f"spanner:///projects/{project}/instances/{instance}/databases/{database}"
        engine = create_engine(url)
        super().__init__(engine)

    async def search_users(self, name: str) -> list[UserSchema]:
        """Spanner は ILIKE 未対応のため、LOWER + LIKE で代替する。"""
        stmt = select(User).where(func.lower(User.name).like(f"%{name.lower()}%"))
        rows = await self._scalars_all(stmt)
        return [UserSchema.model_validate(r) for r in rows]
