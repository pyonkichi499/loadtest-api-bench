# ---- Build stage ----
FROM python:3.13-slim AS builder

WORKDIR /app

# 依存関係ファイルを先にコピー（キャッシュ活用）
COPY pyproject.toml README.md ./

# ソースコードをコピー（hatchling がビルドに必要）
COPY src/ src/

# wheel をビルドして依存関係と共にインストール先を分離
RUN pip install --no-cache-dir --prefix=/install ".[all]"

# ---- Runtime stage ----
FROM python:3.13-slim

WORKDIR /app

# ビルドステージからインストール済みパッケージをコピー
COPY --from=builder /install /usr/local

# ソースコードをコピー
COPY src/ src/

# 非 root ユーザーを作成して切り替え
RUN groupadd --system appuser && \
    useradd --system --gid appuser --no-create-home appuser
USER appuser

EXPOSE 8080

# Cloud Run は PORT 環境変数でポートを指定する
ENV PORT=8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", \"8080\")}/health')"

CMD ["sh", "-c", "uvicorn loadtest_api.main:app --host 0.0.0.0 --port ${PORT}"]
