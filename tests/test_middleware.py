"""TimingMiddleware のテスト。

レスポンスヘッダー X-Process-Time が正しく付与されること、
および構造化ログに必要なフィールドが記録されることを検証する。
"""

import logging

import pytest
from httpx import AsyncClient


# --- レスポンスヘッダー ---


async def test_レスポンスヘッダーにX_Process_Timeが含まれる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    """/health へのリクエストで X-Process-Time ヘッダーが存在することを検証。"""
    client, _ = async_client
    response = await client.get("/health")
    assert response.status_code == 200
    assert "x-process-time" in response.headers


async def test_X_Process_Timeが正の数値である(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    """ヘッダー値が float に変換可能で 0 より大きいことを検証。"""
    client, _ = async_client
    response = await client.get("/health")
    assert response.status_code == 200

    raw_value: str = response.headers["x-process-time"]
    process_time: float = float(raw_value)
    assert process_time > 0


async def test_X_Process_Timeが小数6桁のフォーマットである(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    """ヘッダー値が小数点以下6桁であることを検証。"""
    client, _ = async_client
    response = await client.get("/health")
    raw_value: str = response.headers["x-process-time"]
    parts: list[str] = raw_value.split(".")
    assert len(parts) == 2
    assert len(parts[1]) == 6


@pytest.mark.parametrize(
    "path",
    [
        "/users",
        "/users/stats",
        "/health",
    ],
    ids=["users_list", "users_stats", "health"],
)
async def test_全エンドポイントでX_Process_Timeが付与される(
    async_client: tuple[AsyncClient, list[str]],
    path: str,
) -> None:
    """複数のエンドポイントで X-Process-Time ヘッダーが付与されることを確認。"""
    client, _ = async_client
    response = await client.get(path)
    assert response.status_code == 200
    assert "x-process-time" in response.headers

    raw_value: str = response.headers["x-process-time"]
    process_time: float = float(raw_value)
    assert process_time > 0


async def test_404レスポンスでもX_Process_Timeが付与される(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    """エラーレスポンスでもミドルウェアが動作することを確認。"""
    client, _ = async_client
    response = await client.get("/users/nonexistent-id")
    assert response.status_code == 404
    assert "x-process-time" in response.headers
    process_time: float = float(response.headers["x-process-time"])
    assert process_time > 0


# --- 構造化ログ ---


async def test_ミドルウェアが構造化ログを出力する(
    async_client: tuple[AsyncClient, list[str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """request completed メッセージがログに記録されることを確認。"""
    client, _ = async_client
    with caplog.at_level(logging.INFO):
        await client.get("/health")
    log_messages: list[str] = [r.message for r in caplog.records]
    assert any("request completed" in msg for msg in log_messages)


async def test_ミドルウェアログにmethod_path_status_code_duration_msが含まれる(
    async_client: tuple[AsyncClient, list[str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ログの extra フィールドに必要な情報が全て含まれることを確認。"""
    client, _ = async_client
    with caplog.at_level(logging.INFO):
        await client.get("/health")
    timing_records: list[logging.LogRecord] = [
        r for r in caplog.records if r.message == "request completed"
    ]
    assert len(timing_records) >= 1
    record: logging.LogRecord = timing_records[0]
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/health"  # type: ignore[attr-defined]
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert isinstance(record.duration_ms, float)  # type: ignore[attr-defined]
    assert record.duration_ms >= 0  # type: ignore[attr-defined]
