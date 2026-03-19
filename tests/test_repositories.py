import uuid

from loadtest_api.models.user import UserSchema
from loadtest_api.repositories.base import DBAccessor


# --- get_user_by_id ---


async def test_ユーザーIDで1件取得できる(
    seeded_accessor_with_ids: tuple[DBAccessor, list[str]],
) -> None:
    accessor, ids = seeded_accessor_with_ids
    user = await accessor.get_user_by_id(ids[0])
    assert user is not None
    assert user.id == ids[0]
    assert user.name == "Alice Smith"
    assert user.age == 30
    assert user.email == "alice@example.com"


async def test_存在しないIDはNoneを返す(db_accessor: DBAccessor) -> None:
    user = await db_accessor.get_user_by_id(str(uuid.uuid4()))
    assert user is None


async def test_取得結果がUserSchemaのインスタンスである(
    seeded_accessor_with_ids: tuple[DBAccessor, list[str]],
) -> None:
    accessor, ids = seeded_accessor_with_ids
    user = await accessor.get_user_by_id(ids[0])
    assert isinstance(user, UserSchema)


# --- list_users ---


async def test_一覧取得でlimitが効く(db_accessor: DBAccessor) -> None:
    users = await db_accessor.list_users(limit=2)
    assert len(users) == 2


async def test_limit未指定でデフォルト100件(db_accessor: DBAccessor) -> None:
    users = await db_accessor.list_users()
    assert len(users) == 3  # 全データ3件なので3件返る


async def test_limitがデータ件数を超えてもエラーにならない(db_accessor: DBAccessor) -> None:
    users = await db_accessor.list_users(limit=999)
    assert len(users) == 3


async def test_limit1で1件だけ返る(db_accessor: DBAccessor) -> None:
    users = await db_accessor.list_users(limit=1)
    assert len(users) == 1


async def test_一覧の各要素がUserSchemaである(db_accessor: DBAccessor) -> None:
    users = await db_accessor.list_users()
    for user in users:
        assert isinstance(user, UserSchema)
        assert isinstance(user.id, str)
        assert isinstance(user.name, str)
        assert isinstance(user.age, int)
        assert isinstance(user.email, str)


# --- search_users ---


async def test_名前で部分一致検索できる(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("Alice")
    assert len(users) == 2  # "Alice Smith" と "Charlie Alice Brown"
    names = {u.name for u in users}
    assert "Alice Smith" in names
    assert "Charlie Alice Brown" in names


async def test_検索結果0件は空リストを返す(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("Nonexistent")
    assert users == []


async def test_検索は大文字小文字を区別しない(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("alice")
    assert len(users) == 2
    names = {u.name for u in users}
    assert "Alice Smith" in names
    assert "Charlie Alice Brown" in names


async def test_前方一致で検索できる(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("Ali")
    assert len(users) == 2  # "Alice Smith" と "Charlie Alice Brown"


async def test_後方一致で検索できる(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("Smith")
    assert len(users) == 1
    assert users[0].name == "Alice Smith"


async def test_中間一致で検索できる(db_accessor: DBAccessor) -> None:
    users = await db_accessor.search_users("lic")
    assert len(users) == 2  # "Alice Smith" と "Charlie Alice Brown"


# --- get_stats ---


async def test_統計情報でcountとavg_ageが返る(db_accessor: DBAccessor) -> None:
    stats = await db_accessor.get_stats()
    assert stats.count == 3
    assert stats.avg_age is not None
    assert abs(stats.avg_age - 30.0) < 0.01  # (30 + 25 + 35) / 3 = 30.0


async def test_データ0件の統計情報(empty_db_accessor: DBAccessor) -> None:
    stats = await empty_db_accessor.get_stats()
    assert stats.count == 0
    assert stats.avg_age is None


async def test_データ1件の統計情報でavg_ageがその値自体になる(
    single_record_accessor: tuple[DBAccessor, str],
) -> None:
    accessor, _ = single_record_accessor
    stats = await accessor.get_stats()
    assert stats.count == 1
    assert stats.avg_age is not None
    assert abs(stats.avg_age - 42.0) < 0.01
