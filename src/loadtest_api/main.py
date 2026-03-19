from fastapi import FastAPI

from loadtest_api.api.users import router

app = FastAPI(
    title="Load Test API",
    description="Load testing API backend for comparing Cloud SQL / Spanner / BigQuery response characteristics",
    version="0.1.0",
)

app.include_router(router)
