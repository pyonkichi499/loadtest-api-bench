import uuid

from httpx import AsyncClient


# --- /health ---


async def test_healthチェックで200が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- GET /users/{user_id} ---


async def test_GET_users_idで200が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, ids = async_client
    response = await client.get(f"/users/{ids[0]}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ids[0]
    assert data["name"] == "Alice Smith"
    assert data["age"] == 30
    assert data["email"] == "alice@example.com"


async def test_存在しないIDで404が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# --- GET /users ---


async def test_GET_usersでリスト取得できる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


async def test_GET_usersのレスポンスに全フィールドが含まれる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    user = data[0]
    assert "id" in user
    assert "name" in user
    assert "age" in user
    assert "email" in user


async def test_limitにマイナス値で422が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=-1")
    assert response.status_code == 422


async def test_limit0で422が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=0")
    assert response.status_code == 422


async def test_limit1001で422が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=1001")
    assert response.status_code == 422


async def test_limit1で200が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_limit1000で200が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users?limit=1000")
    assert response.status_code == 200


# --- GET /users/search ---


async def test_GET_users_searchで検索できる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users/search?name=Alice")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_searchでnameパラメータ未指定は422が返る(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users/search")
    assert response.status_code == 422


async def test_searchで該当なしは空配列を返す(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users/search?name=Zzzzz")
    assert response.status_code == 200
    assert response.json() == []


# --- GET /users/stats ---


async def test_GET_users_statsで統計取得できる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert abs(data["avg_age"] - 30.0) < 0.01


async def test_GET_users_statsのレスポンスに全フィールドが含まれる(
    async_client: tuple[AsyncClient, list[str]],
) -> None:
    client, _ = async_client
    response = await client.get("/users/stats")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "avg_age" in data
