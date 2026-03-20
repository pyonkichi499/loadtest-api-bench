#!/usr/bin/env bash
# ==============================================================================
# Cloud Run デプロイスクリプト
# Usage: ./deploy.sh [cloud_sql|spanner|bigquery]
# ==============================================================================
set -euo pipefail

# ---------------------
# 環境変数の必須チェック関数
# ---------------------
require_env() {
    local var_name="$1"
    if [[ -z "${!var_name:-}" ]]; then
        echo "Error: ${var_name} is required but not set" >&2
        exit 1
    fi
}

# ---------------------
# 設定
# ---------------------
require_env GCP_PROJECT_ID
PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-northeast1}"
SERVICE_NAME_PREFIX="loadtest-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME_PREFIX}"

# ---------------------
# 引数チェック
# ---------------------
DB_TYPE="${1:-}"
if [[ -z "${DB_TYPE}" ]]; then
    echo "Usage: $0 [cloud_sql|spanner|bigquery]"
    echo ""
    echo "Examples:"
    echo "  $0 cloud_sql    # Cloud SQL 版をデプロイ"
    echo "  $0 spanner      # Spanner 版をデプロイ"
    echo "  $0 bigquery     # BigQuery 版をデプロイ"
    exit 1
fi

case "${DB_TYPE}" in
    cloud_sql|spanner|bigquery)
        ;;
    *)
        echo "Error: DB_TYPE は cloud_sql, spanner, bigquery のいずれかを指定してください"
        exit 1
        ;;
esac

SERVICE_NAME="${SERVICE_NAME_PREFIX}-${DB_TYPE//_/-}"

echo "================================================"
echo "Deploying ${SERVICE_NAME} to Cloud Run"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  DB Type:  ${DB_TYPE}"
echo "================================================"

# ---------------------
# Docker イメージのビルドとプッシュ
# ---------------------
echo ""
echo "[1/2] Building and pushing Docker image..."
gcloud builds submit \
    --project "${PROJECT_ID}" \
    --tag "${IMAGE_NAME}:latest" \
    .

# ---------------------
# 共通の環境変数
# ---------------------
ENV_VARS="APP_DB_TYPE=${DB_TYPE},APP_LOG_FORMAT=json"

# ---------------------
# DB タイプ別の設定
# ---------------------
EXTRA_FLAGS=()

case "${DB_TYPE}" in
    cloud_sql)
        # Cloud SQL 用の環境変数
        # DSN 形式: postgresql+asyncpg://user:password@/dbname?host=/cloudsql/project:region:instance
        require_env APP_CLOUD_SQL_DSN
        require_env CLOUD_SQL_INSTANCE_CONNECTION
        ENV_VARS="${ENV_VARS},APP_CLOUD_SQL_DSN=${APP_CLOUD_SQL_DSN}"
        EXTRA_FLAGS+=(--add-cloudsql-instances "${CLOUD_SQL_INSTANCE_CONNECTION}")
        ;;
    spanner)
        require_env APP_SPANNER_PROJECT
        require_env APP_SPANNER_INSTANCE
        require_env APP_SPANNER_DATABASE
        ENV_VARS="${ENV_VARS},APP_SPANNER_PROJECT=${APP_SPANNER_PROJECT}"
        ENV_VARS="${ENV_VARS},APP_SPANNER_INSTANCE=${APP_SPANNER_INSTANCE}"
        ENV_VARS="${ENV_VARS},APP_SPANNER_DATABASE=${APP_SPANNER_DATABASE}"
        ;;
    bigquery)
        require_env APP_BIGQUERY_PROJECT
        require_env APP_BIGQUERY_DATASET
        ENV_VARS="${ENV_VARS},APP_BIGQUERY_PROJECT=${APP_BIGQUERY_PROJECT}"
        ENV_VARS="${ENV_VARS},APP_BIGQUERY_DATASET=${APP_BIGQUERY_DATASET}"
        ;;
esac

# ---------------------
# Cloud Run デプロイ
# ---------------------
echo ""
echo "[2/2] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --project "${PROJECT_ID}" \
    --image "${IMAGE_NAME}:latest" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 60 \
    --set-env-vars "${ENV_VARS}" \
    "${EXTRA_FLAGS[@]}"

# ---------------------
# デプロイ結果の表示
# ---------------------
echo ""
echo "================================================"
echo "Deployment complete!"
echo ""

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format "value(status.url)")

echo "Service URL: ${SERVICE_URL}"
echo "Health check: ${SERVICE_URL}/health"
echo "API docs:     ${SERVICE_URL}/docs"
echo "================================================"
