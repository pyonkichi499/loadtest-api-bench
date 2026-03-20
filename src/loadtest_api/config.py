from typing import Literal

from pydantic_settings import BaseSettings

DB_TYPE = Literal["sqlite", "cloud_sql", "spanner", "bigquery"]


class Settings(BaseSettings):
    db_type: DB_TYPE = "sqlite"
    sqlite_path: str = ":memory:"
    cloud_sql_dsn: str = ""
    spanner_project: str = ""
    spanner_instance: str = ""
    spanner_database: str = ""
    bigquery_project: str = ""
    bigquery_dataset: str = ""
    log_format: str = "text"

    # コネクションプール設定 (Cloud SQL 用)
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    model_config = {"env_prefix": "APP_"}


def get_settings() -> Settings:
    return Settings()
