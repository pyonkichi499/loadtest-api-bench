from functools import lru_cache

from fastapi import Depends

from loadtest_api.config import Settings, get_settings
from loadtest_api.repositories.base import DBAccessor


@lru_cache
def _create_accessor(
    db_type: str,
    sqlite_path: str = ":memory:",
    cloud_sql_dsn: str = "",
    spanner_project: str = "",
    spanner_instance: str = "",
    spanner_database: str = "",
    bigquery_project: str = "",
    bigquery_dataset: str = "",
) -> DBAccessor:
    match db_type:
        case "sqlite":
            from loadtest_api.repositories.sqlite import SQLiteAccessor
            return SQLiteAccessor(path=sqlite_path)
        case "cloud_sql":
            from loadtest_api.repositories.cloud_sql import CloudSQLAccessor
            return CloudSQLAccessor(dsn=cloud_sql_dsn)
        case "spanner":
            from loadtest_api.repositories.spanner import SpannerAccessor
            return SpannerAccessor(
                project=spanner_project,
                instance=spanner_instance,
                database=spanner_database,
            )
        case "bigquery":
            from loadtest_api.repositories.bigquery import BigQueryAccessor
            return BigQueryAccessor(
                project=bigquery_project,
                dataset=bigquery_dataset,
            )
        case _:
            raise ValueError(f"Unsupported db_type: {db_type}")


def get_db_accessor(settings: Settings = Depends(get_settings)) -> DBAccessor:
    return _create_accessor(
        settings.db_type,
        sqlite_path=settings.sqlite_path,
        cloud_sql_dsn=settings.cloud_sql_dsn,
        spanner_project=settings.spanner_project,
        spanner_instance=settings.spanner_instance,
        spanner_database=settings.spanner_database,
        bigquery_project=settings.bigquery_project,
        bigquery_dataset=settings.bigquery_dataset,
    )
