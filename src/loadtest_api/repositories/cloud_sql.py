from sqlalchemy.ext.asyncio import create_async_engine

from loadtest_api.repositories.async_accessor import AsyncDBAccessor


class CloudSQLAccessor(AsyncDBAccessor):
    def __init__(
        self,
        dsn: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
    ) -> None:
        engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )
        super().__init__(engine)
