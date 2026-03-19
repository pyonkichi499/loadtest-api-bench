from sqlalchemy.ext.asyncio import create_async_engine

from loadtest_api.repositories.async_accessor import AsyncDBAccessor


class SQLiteAccessor(AsyncDBAccessor):
    def __init__(self, path: str = ":memory:") -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}", echo=False)
        super().__init__(engine)
