"""シードデータ生成スクリプト

Usage:
    rye run python scripts/seed.py --db-type sqlite --sqlite-path seed.db --count 100000
"""
import random
import uuid

import click
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from loadtest_api.models.user import Base


def _generate_uuid4(rng: random.Random) -> str:
    """再現可能な UUID4 を生成する。"""
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def generate_users(count: int, seed: int | None = None) -> list[dict[str, str | int]]:
    """Faker を使ってユーザーデータを生成する。

    Args:
        count: 生成するユーザー数
        seed: Faker のシード値（再現性のため）

    Returns:
        ユーザーデータの辞書リスト
    """
    fake = Faker()
    if seed is not None:
        Faker.seed(seed)
        rng = random.Random(seed)
    else:
        rng = random.Random()

    users: list[dict[str, str | int]] = []
    seen_emails: set[str] = set()

    for i in range(count):
        user_id: str = _generate_uuid4(rng)
        name: str = fake.name()
        age: int = fake.random_int(min=18, max=80)

        # email を一意にするためにインデックスを付与
        base_email: str = f"user{i}@{fake.domain_name()}"
        while base_email in seen_emails:
            base_email = f"user{i}_{fake.random_int(min=1000, max=9999)}@{fake.domain_name()}"
        seen_emails.add(base_email)

        users.append({
            "id": user_id,
            "name": name,
            "age": age,
            "email": base_email,
        })

    return users


def _seed_sqlite(sqlite_path: str, count: int, batch_size: int, seed: int | None) -> None:
    """SQLite にシードデータを投入する。"""
    engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)

    # DROP → CREATE
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    click.echo(f"テーブルを作成しました: {sqlite_path}")

    # データ生成
    click.echo(f"ユーザーデータを生成中... (count={count})")
    users = generate_users(count=count, seed=seed)

    # バッチ挿入
    click.echo(f"データを挿入中... (batch_size={batch_size})")
    with Session(engine) as session:
        with click.progressbar(length=count, label="Inserting") as bar:
            for i in range(0, count, batch_size):
                batch = users[i:i + batch_size]
                session.execute(
                    text(
                        "INSERT INTO users (id, name, age, email) "
                        "VALUES (:id, :name, :age, :email)"
                    ),
                    batch,
                )
                session.commit()
                bar.update(len(batch))

    engine.dispose()
    click.echo(f"完了: {count} 件のユーザーデータを投入しました。")


@click.command()
@click.option("--db-type", type=click.Choice(["sqlite"]), required=True, help="対象 DB タイプ")
@click.option("--sqlite-path", type=str, default="seed.db", help="SQLite ファイルパス")
@click.option("--count", type=click.IntRange(min=0), default=100_000, help="生成するレコード数")
@click.option("--batch-size", type=click.IntRange(min=1), default=1000, help="バッチ挿入サイズ")
@click.option("--seed", type=int, default=None, help="Faker シード値（再現性のため）")
def cli(db_type: str, sqlite_path: str, count: int, batch_size: int, seed: int | None) -> None:
    """シードデータを生成して DB に投入するスクリプト。"""
    click.echo(f"DB Type: {db_type}")
    click.echo(f"Count: {count}")

    if db_type == "sqlite":
        _seed_sqlite(sqlite_path, count, batch_size, seed)
    else:
        raise click.ClickException(f"未対応の DB タイプ: {db_type}")


if __name__ == "__main__":
    cli()
