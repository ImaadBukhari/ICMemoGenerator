#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="icmemo-backend"
REPO_NAME="docker-repo"

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

cd "$(dirname "$0")/.."

echo "🔧 Building amd64 image for Cloud Run..."
docker buildx build --platform linux/amd64 -t $IMAGE_URI --push .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION

echo "✅ Deployment complete!"
