#!/bin/bash

# Configuration
PROJECT_ID="icmemogenerator"
REGION="us-central1"
INSTANCE_NAME="icmemo-postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting deployment to Google Cloud with Cloud SQL...${NC}"

# Set the project
echo -e "${YELLOW}📋 Setting project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Get Cloud SQL connection name
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)" --project=$PROJECT_ID)
echo -e "${GREEN}Cloud SQL Connection: $CONNECTION_NAME${NC}"

# Setup Docker buildx for multi-platform builds
echo -e "${YELLOW}🔧 Setting up Docker buildx...${NC}"
docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch

# Build and push backend image for AMD64
echo -e "${YELLOW}🏗️  Building backend image for AMD64...${NC}"
docker buildx build \
    --platform linux/amd64 \
    -t gcr.io/$PROJECT_ID/icmemo-backend:latest \
    -f infra/Dockerfile.backend \
    --push \
    .

# Deploy backend service with Cloud SQL connection
echo -e "${YELLOW}🚢 Deploying backend service with Cloud SQL...${NC}"
gcloud run deploy icmemo-backend \
    --image gcr.io/$PROJECT_ID/icmemo-backend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --service-account cloud-run-sql-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production \
    --set-secrets DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,OPENAI_API_KEY=openai-api-key:latest,AFFINITY_API_KEY=affinity-api-key:latest,PERPLEXITY_API_KEY=perplexity-api-key:latest

# Get backend URL
BACKEND_URL=$(gcloud run services describe icmemo-backend --region=$REGION --format="value(status.url)")
echo -e "${GREEN}Backend deployed at: $BACKEND_URL${NC}"

# Build and push frontend image with backend URL
echo -e "${YELLOW}🏗️  Building frontend image with API URL: $BACKEND_URL${NC}"
docker buildx build \
    --platform linux/amd64 \
    --build-arg REACT_APP_API_URL=$BACKEND_URL \
    -t gcr.io/$PROJECT_ID/icmemo-frontend:latest \
    -f infra/Dockerfile.frontend \
    --push \
    .

# Deploy frontend service
echo -e "${YELLOW}🚢 Deploying frontend service...${NC}"
gcloud run deploy icmemo-frontend \
    --image gcr.io/$PROJECT_ID/icmemo-frontend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars REACT_APP_API_URL=$BACKEND_URL

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe icmemo-frontend --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🔗 Backend URL: $BACKEND_URL${NC}"
echo -e "${GREEN}🔗 Frontend URL: $FRONTEND_URL${NC}"

echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Update your Google OAuth redirect URI to: $BACKEND_URL/api/auth/google/callback"
echo "2. Run database migrations"
echo ""
echo "To run migrations:"
echo "  cloud-sql-proxy $CONNECTION_NAME &"
echo "  cd backend && alembic upgrade head"