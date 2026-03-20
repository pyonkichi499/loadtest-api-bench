import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger: logging.Logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """全リクエストの処理時間を計測し、レスポンスヘッダーとログに記録するミドルウェア。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start: float = time.perf_counter()
        response: Response = await call_next(request)
        duration: float = time.perf_counter() - start

        response.headers["X-Process-Time"] = f"{duration:.6f}"

        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response
