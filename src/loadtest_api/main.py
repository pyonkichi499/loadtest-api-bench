from fastapi import FastAPI

from loadtest_api.api.users import router
from loadtest_api.config import get_settings
from loadtest_api.logging import setup_logging
from loadtest_api.middleware import TimingMiddleware

settings = get_settings()
setup_logging(settings.log_format)

app = FastAPI(
    title="Load Test API",
    description="Load testing API backend for comparing Cloud SQL / Spanner / BigQuery response characteristics",
    version="0.1.0",
)

app.add_middleware(TimingMiddleware)
app.include_router(router)
