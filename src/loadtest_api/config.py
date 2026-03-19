from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_type: str = "sqlite"
    sqlite_path: str = ":memory:"
    cloud_sql_dsn: str = ""
    spanner_project: str = ""
    spanner_instance: str = ""
    spanner_database: str = ""
    bigquery_project: str = ""
    bigquery_dataset: str = ""
    log_format: str = "text"

    model_config = {"env_prefix": "APP_"}


def get_settings() -> Settings:
    return Settings()
