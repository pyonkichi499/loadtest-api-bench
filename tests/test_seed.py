"""シードデータ生成スクリプトのテスト"""
import os
import tempfile
import uuid

from click.testing import CliRunner
from sqlalchemy import create_engine, text

from scripts.seed import cli, generate_users


class TestGenerateUsers:
    """generate_users 関数のテスト"""

    def test_指定件数のユーザーデータを生成できる(self) -> None:
        users = generate_users(count=10, seed=42)
        assert len(users) == 10

    def test_生成されたユーザーデータにすべてのフィールドが含まれる(self) -> None:
        users = generate_users(count=1, seed=42)
        user = users[0]
        assert "id" in user
        assert "name" in user
        assert "age" in user
        assert "email" in user

    def test_IDがUUID4形式である(self) -> None:
        users = generate_users(count=5, seed=42)
        for user in users:
            parsed = uuid.UUID(user["id"])
            assert parsed.version == 4, f"Expected UUID v4, got v{parsed.version}"

    def test_年齢が18から80の範囲内である(self) -> None:
        users = generate_users(count=100, seed=42)
        for user in users:
            assert 18 <= user["age"] <= 80

    def test_メールアドレスが一意である(self) -> None:
        users = generate_users(count=1000, seed=42)
        emails = [u["email"] for u in users]
        assert len(emails) == len(set(emails))

    def test_シードを指定すると再現可能なデータが生成される(self) -> None:
        users_a = generate_users(count=10, seed=123)
        users_b = generate_users(count=10, seed=123)
        assert users_a == users_b

    def test_名前が空文字でない(self) -> None:
        users = generate_users(count=10, seed=42)
        for user in users:
            assert len(user["name"]) > 0

    def test_メールアドレスにアットマークが含まれる(self) -> None:
        users = generate_users(count=10, seed=42)
        for user in users:
            assert "@" in user["email"]


class TestCLISqlite:
    """CLI の SQLite モードのテスト"""

    def test_SQLiteにシードデータを投入できる(self) -> None:
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "100",
                "--seed", "42",
            ])
            assert result.exit_code == 0, f"CLI failed: {result.output}"

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                row = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                assert row == 100
            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_既存テーブルがある場合にDROPしてから再作成する(self) -> None:
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # 1回目: 50件投入
            result1 = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "50",
                "--seed", "42",
            ])
            assert result1.exit_code == 0

            # 2回目: 30件投入（DROP → CREATE → INSERT）
            result2 = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "30",
                "--seed", "99",
            ])
            assert result2.exit_code == 0

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                row = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                # 蓄積ではなく30件のみ
                assert row == 30
            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_バッチ挿入で大量データを投入できる(self) -> None:
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "2500",
                "--seed", "42",
            ])
            assert result.exit_code == 0, f"CLI failed: {result.output}"

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                row = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                assert row == 2500
            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_count0で空のテーブルが作成される(self) -> None:
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "0",
                "--seed", "42",
            ])
            assert result.exit_code == 0, f"CLI failed: {result.output}"

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                row = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                assert row == 0
            engine.dispose()
        finally:
            os.unlink(db_path)

    def test_batch_size0でエラーになる(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--db-type", "sqlite",
            "--count", "10",
            "--batch-size", "0",
        ])
        assert result.exit_code != 0

    def test_countに負数を指定するとエラーになる(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--db-type", "sqlite",
            "--count", "-1",
        ])
        assert result.exit_code != 0

    def test_未対応のDBタイプでエラーになる(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--db-type", "spanner",
            "--count", "10",
        ])
        assert result.exit_code != 0

    def test_投入されたデータの内容が正しい(self) -> None:
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = runner.invoke(cli, [
                "--db-type", "sqlite",
                "--sqlite-path", db_path,
                "--count", "10",
                "--seed", "42",
            ])
            assert result.exit_code == 0

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT id, name, age, email FROM users")).fetchall()
                assert len(rows) == 10
                for row in rows:
                    # UUID v4 形式チェック
                    parsed_uuid = uuid.UUID(row[0])
                    assert parsed_uuid.version == 4, f"Expected UUID v4, got v{parsed_uuid.version}"
                    # name が空でない
                    assert len(row[1]) > 0
                    # age が範囲内
                    assert 18 <= row[2] <= 80
                    # email に @ が含まれる
                    assert "@" in row[3]
            engine.dispose()
        finally:
            os.unlink(db_path)
