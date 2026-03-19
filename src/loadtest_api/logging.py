import json
import logging
import sys
from datetime import datetime, timezone


class CloudLoggingFormatter(logging.Formatter):
    """Cloud Logging 互換の構造化 JSON フォーマッタ。"""

    _LEVEL_TO_SEVERITY: dict[str, str] = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARNING": "WARNING",
        "ERROR": "ERROR",
        "CRITICAL": "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, str] = {
            "severity": self._LEVEL_TO_SEVERITY.get(record.levelname, record.levelname),
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_format: str) -> None:
    """アプリケーション全体のログ設定を初期化する。

    Args:
        log_format: "json" で Cloud Logging 向け構造化 JSON、
                    "text" で人間が読みやすいテキスト形式。
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    if log_format == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CloudLoggingFormatter())
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # uvicorn のログも統一する
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
