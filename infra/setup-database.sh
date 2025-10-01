#!/bin/bash

PROJECT_ID="icmemogenerator"
REGION="us-central1"
INSTANCE_NAME="icmemo-postgres"
DATABASE_NAME="icmemo"
DB_USER="icmemo_user"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Generate a random password
DB_PASSWORD=$(openssl rand -base64 32)

echo -e "${YELLOW}🗄️  Setting up Cloud SQL PostgreSQL instance...${NC}"

# Create Cloud SQL instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup \
    --backup-start-time=03:00 \
    --project=$PROJECT_ID

# Create database
gcloud sql databases create $DATABASE_NAME \
    --instance=$INSTANCE_NAME \
    --project=$PROJECT_ID

# Create user
gcloud sql users create $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=$DB_PASSWORD \
    --project=$PROJECT_ID

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)" --project=$PROJECT_ID)

echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Your database connection details:${NC}"
echo "Connection Name: $CONNECTION_NAME"  
echo "Database: $DATABASE_NAME"
echo "User: $DB_USER"
echo "Password: $DB_PASSWORD"
echo ""
echo -e "${YELLOW}🔐 DATABASE_URL for Cloud Run (use this in setup-secrets.sh):${NC}"
echo "postgresql://$DB_USER:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME"
echo ""
echo -e "${YELLOW}📝 For local development with Cloud SQL Proxy:${NC}"
echo "1. Install Cloud SQL Proxy: gcloud components install cloud-sql-proxy"
echo "2. Start proxy: cloud-sql-proxy $CONNECTION_NAME"
echo "3. Use DATABASE_URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DATABASE_NAME"