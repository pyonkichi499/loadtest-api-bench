"""CloudLoggingFormatter のテスト。

extra フィールドが JSON 出力に正しく含まれることを検証する。
"""

import json
import logging

from loadtest_api.logging import CloudLoggingFormatter


def test_extraフィールドがJSONに含まれる() -> None:
    """extra に渡した method, path 等が JSON 出力に含まれることを確認。"""
    formatter: CloudLoggingFormatter = CloudLoggingFormatter()
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.method = "GET"  # type: ignore[attr-defined]
    record.path = "/health"  # type: ignore[attr-defined]
    record.status_code = 200  # type: ignore[attr-defined]
    record.duration_ms = 1.23  # type: ignore[attr-defined]

    output: str = formatter.format(record)
    data: dict = json.loads(output)

    assert data["method"] == "GET"
    assert data["path"] == "/health"
    assert data["status_code"] == 200
    assert data["duration_ms"] == 1.23


def test_extraフィールドがない場合でもフォーマットできる() -> None:
    """extra がない通常のログレコードでもエラーにならないことを確認。"""
    formatter: CloudLoggingFormatter = CloudLoggingFormatter()
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="simple message",
        args=(),
        exc_info=None,
    )

    output: str = formatter.format(record)
    data: dict = json.loads(output)

    assert data["message"] == "simple message"
    assert data["severity"] == "INFO"
    # 標準の LogRecord 属性は extra として出力されないことを確認
    assert "name" not in data or data.get("name") != "test"


def test_extraの標準属性は出力に含まれない() -> None:
    """LogRecord の標準属性 (levelname 等) が extra として重複出力されないことを確認。"""
    formatter: CloudLoggingFormatter = CloudLoggingFormatter()
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="/some/path.py",
        lineno=42,
        msg="warning message",
        args=(),
        exc_info=None,
    )

    output: str = formatter.format(record)
    data: dict = json.loads(output)

    assert "levelname" not in data
    assert "pathname" not in data
    assert "lineno" not in data
    assert "args" not in data
