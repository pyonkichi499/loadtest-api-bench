from sqlalchemy import create_engine

from loadtest_api.repositories.sync_accessor import SyncDBAccessor


class BigQueryAccessor(SyncDBAccessor):
    def __init__(self, project: str, dataset: str) -> None:
        engine = create_engine(f"bigquery://{project}/{dataset}")
        super().__init__(engine)
