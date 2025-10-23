#!/bin/bash
set -e

PROJECT_ID="icmemogenerator-475014"
REGION="us-central1"
SERVICE_NAME="icmemo-backend"
IMAGE_URI="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

cd "$(dirname "$0")/.."

echo "🔧 Building with Cloud Build..."
gcloud builds submit --tag $IMAGE_URI .

echo "🚀 Deploying to Cloud Run with environment variables..."

# Read values from backend/.env file if it exists
if [ -f "backend/.env" ]; then
    echo "📖 Reading values from backend/.env..."
    source backend/.env
else
    echo "⚠️  backend/.env not found, using default values"
    # Set default values or prompt for them
    OPENAI_API_KEY=${OPENAI_API_KEY:-"your_openai_api_key"}
    AFFINITY_API_KEY=${AFFINITY_API_KEY:-"your_affinity_api_key"}
    GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-"your_google_client_id"}
    GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-"your_google_client_secret"}
    PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-"your_perplexity_api_key"}
fi

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION \
  --add-cloudsql-instances=${PROJECT_ID}:${REGION}:icmemo-db \
  --set-env-vars="DATABASE_URL=postgresql://icmemo_user:ilikedeals123%21@/icmemo_db?host=/cloudsql/icmemogenerator-475014:us-central1:icmemo-db,OPENAI_API_KEY=${OPENAI_API_KEY},AFFINITY_API_KEY=${AFFINITY_API_KEY},GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID},GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET},PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY},FRONTEND_URL=https://icmemogenerator.web.app,ALLOWED_DOMAIN=wyldvc.com"

echo "✅ Deployment complete!"