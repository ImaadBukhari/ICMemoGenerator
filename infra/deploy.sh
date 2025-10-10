#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="icmemo-backend"

# Get secrets
OPENAI_KEY=$(gcloud secrets versions access latest --secret="openai-api-key")
PERPLEXITY_KEY=$(gcloud secrets versions access latest --secret="perplexity-api-key")
AFFINITY_KEY=$(gcloud secrets versions access latest --secret="affinity-api-key")
GOOGLE_CLIENT_ID=$(gcloud secrets versions access latest --secret="google-client-id")
GOOGLE_CLIENT_SECRET=$(gcloud secrets versions access latest --secret="google-client-secret")
JWT_SECRET=$(gcloud secrets versions access latest --secret="jwt-secret-key")
DATABASE_URL=$(gcloud secrets versions access latest --secret="database-url")

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/icmemo-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars "OPENAI_API_KEY=${OPENAI_KEY}" \
  --set-env-vars "PERPLEXITY_API_KEY=${PERPLEXITY_KEY}" \
  --set-env-vars "AFFINITY_API_KEY=${AFFINITY_KEY}" \
  --set-env-vars "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
  --set-env-vars "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
  --set-env-vars "SECRET_KEY=${JWT_SECRET}" \
  --set-env-vars "ALGORITHM=HS256" \
  --set-env-vars "ACCESS_TOKEN_EXPIRE_MINUTES=1440" \
  --cpu 1 \
  --memory 512Mi \
  --timeout 3600 \
  --max-instances 3 \
  --min-instances 0 \
  --concurrency 100

echo "Deployment complete!"
echo "Backend URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')"