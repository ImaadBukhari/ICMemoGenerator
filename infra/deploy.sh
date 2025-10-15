#!/bin/bash

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="icmemo-backend"

echo "Deploying to Cloud Run..."

# Just deploy the new image - keep existing env vars
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/icmemo-backend \
  --region $REGION \
  --allow-unauthenticated

echo "Deployment complete!"