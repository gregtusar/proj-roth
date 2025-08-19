#!/bin/bash

# Setup script for Google OAuth credentials
# This script helps configure OAuth for the NJ Voter Chat application

PROJECT_ID="proj-roth"
REGION="us-central1"

echo "Setting up Google OAuth for NJ Voter Chat..."
echo "==========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

echo ""
echo "To set up OAuth, you need to:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Click 'CREATE CREDENTIALS' > 'OAuth client ID'"
echo "3. Choose 'Web application' as the application type"
echo "4. Set the name to 'NJ Voter Chat OAuth'"
echo "5. Add authorized redirect URIs:"
echo "   - http://localhost:8501 (for local development)"
echo "   - https://YOUR-CLOUD-RUN-URL (for production)"
echo "6. Copy the Client ID and Client Secret"
echo ""

read -p "Enter your OAuth Client ID: " CLIENT_ID
read -sp "Enter your OAuth Client Secret: " CLIENT_SECRET
echo ""
read -p "Enter JWT Secret Key (or press Enter to generate): " JWT_SECRET

if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    echo "Generated JWT Secret: $JWT_SECRET"
fi

echo ""
echo "Storing secrets in Google Secret Manager..."

# Create secrets in Secret Manager
echo "$CLIENT_ID" | gcloud secrets create google-oauth-client-id --data-file=- --replication-policy="automatic" 2>/dev/null || \
    echo "$CLIENT_ID" | gcloud secrets versions add google-oauth-client-id --data-file=-

echo "$CLIENT_SECRET" | gcloud secrets create google-oauth-client-secret --data-file=- --replication-policy="automatic" 2>/dev/null || \
    echo "$CLIENT_SECRET" | gcloud secrets versions add google-oauth-client-secret --data-file=-

echo "$JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=- --replication-policy="automatic" 2>/dev/null || \
    echo "$JWT_SECRET" | gcloud secrets versions add jwt-secret-key --data-file=-

echo ""
echo "Secrets stored successfully!"
echo ""

# Create the user table in BigQuery
echo "Creating authorized_users table in BigQuery..."
bq query --use_legacy_sql=false < config/user_table_schema.sql

echo ""
echo "Adding initial admin user..."
read -p "Enter admin email address: " ADMIN_EMAIL

if [ -n "$ADMIN_EMAIL" ]; then
    bq query --use_legacy_sql=false "
    INSERT INTO \`proj-roth.voter_data.authorized_users\` (
        user_id,
        email,
        full_name,
        is_active,
        role
    ) VALUES (
        GENERATE_UUID(),
        '$ADMIN_EMAIL',
        'Admin User',
        TRUE,
        'admin'
    )"
    echo "Admin user added: $ADMIN_EMAIL"
fi

echo ""
echo "OAuth setup complete!"
echo ""
echo "For local development, export these environment variables:"
echo "export GOOGLE_OAUTH_CLIENT_ID=$CLIENT_ID"
echo "export GOOGLE_OAUTH_CLIENT_SECRET=$CLIENT_SECRET"
echo "export JWT_SECRET_KEY=$JWT_SECRET"
echo "export OAUTH_REDIRECT_URI=http://localhost:8501"
echo ""
echo "For production deployment, these secrets will be accessed from Secret Manager."