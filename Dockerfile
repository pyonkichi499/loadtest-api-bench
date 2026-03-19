FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir ".[all]"

EXPOSE 8080

CMD ["uvicorn", "loadtest_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
