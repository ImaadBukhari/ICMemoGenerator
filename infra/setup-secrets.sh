#!/bin/bash

PROJECT_ID="icmemogenerator"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔐 Setting up secrets in Google Secret Manager...${NC}"

gcloud config set project $PROJECT_ID

echo -e "${YELLOW}Creating secrets...${NC}"

# Database URL (from Cloud SQL setup)
echo "Enter your DATABASE_URL (from setup-database.sh output):"
echo "Format: postgresql://user:password@/database?host=/cloudsql/project:region:instance"
read -s DATABASE_URL
echo -n "$DATABASE_URL" | gcloud secrets create database-url --data-file=-

# Google OAuth
echo "Enter your GOOGLE_CLIENT_ID:"
read GOOGLE_CLIENT_ID
echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id --data-file=-

echo "Enter your GOOGLE_CLIENT_SECRET:"
read -s GOOGLE_CLIENT_SECRET
echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-

# API Keys
echo "Enter your OPENAI_API_KEY:"
read -s OPENAI_API_KEY
echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-

echo "Enter your AFFINITY_API_KEY:"
read -s AFFINITY_API_KEY
echo -n "$AFFINITY_API_KEY" | gcloud secrets create affinity-api-key --data-file=-

echo "Enter your PERPLEXITY_API_KEY:"
read -s PERPLEXITY_API_KEY
echo -n "$PERPLEXITY_API_KEY" | gcloud secrets create perplexity-api-key --data-file=-

echo -e "${GREEN}✅ Secrets created successfully!${NC}"