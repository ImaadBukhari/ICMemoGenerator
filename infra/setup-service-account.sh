#!/bin/bash

PROJECT_ID="icmemogenerator"
SERVICE_ACCOUNT_NAME="cloud-run-sql-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔑 Setting up service account for Cloud Run...${NC}"

# Create service account
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Cloud Run SQL Service Account" \
    --project=$PROJECT_ID

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/cloudsql.client"

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

echo -e "${GREEN}✅ Service account created and configured!${NC}"
echo "Service Account: ${SERVICE_ACCOUNT_EMAIL}"