#!/bin/bash

# Setup script for voter lists feature
# Creates service account, BigQuery table, and necessary permissions

set -e

PROJECT_ID="proj-roth"
DATASET_ID="voter_data"
TABLE_ID="voter_lists"
SERVICE_ACCOUNT_NAME="voter-lists-writer"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Setting up Voter Lists feature..."

# 1. Create service account for voter lists writer
echo "Creating service account ${SERVICE_ACCOUNT_NAME}..."
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="Voter Lists Writer" \
    --description="Service account for writing to voter_lists table" \
    --project=${PROJECT_ID} || echo "Service account already exists"

# 2. Grant BigQuery permissions to the service account
echo "Granting BigQuery permissions..."

# Grant read access to the entire dataset (to read voters table)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/bigquery.dataViewer" || true

# Grant job user role to run queries
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/bigquery.jobUser" || true

# 3. Create the voter_lists table
echo "Creating voter_lists table in BigQuery..."
bq query --use_legacy_sql=false --project_id=${PROJECT_ID} < config/voter_lists_schema.sql || echo "Table might already exist"

# 4. Grant specific write permissions to voter_lists table only
echo "Granting write permissions to voter_lists table..."
bq update --project_id=${PROJECT_ID} \
    --set_iam_policy \
    <(echo '{
      "bindings": [
        {
          "role": "roles/bigquery.dataEditor",
          "members": ["serviceAccount:'${SERVICE_ACCOUNT_EMAIL}'"]
        }
      ]
    }') \
    ${DATASET_ID}.${TABLE_ID} || echo "Permissions might already be set"

# 5. Create service account key for local development (optional)
echo "Creating service account key..."
KEY_FILE="keys/voter-lists-writer-key.json"
mkdir -p keys
gcloud iam service-accounts keys create ${KEY_FILE} \
    --iam-account=${SERVICE_ACCOUNT_EMAIL} \
    --project=${PROJECT_ID} || echo "Key might already exist"

echo "Setup complete!"
echo "Service account: ${SERVICE_ACCOUNT_EMAIL}"
echo "Table: ${PROJECT_ID}.${DATASET_ID}.${TABLE_ID}"
echo "Key file: ${KEY_FILE}"

# 6. Store service account email in Secret Manager for Cloud Run
echo "Storing service account info in Secret Manager..."
echo ${SERVICE_ACCOUNT_EMAIL} | gcloud secrets create voter-lists-writer-sa \
    --data-file=- \
    --project=${PROJECT_ID} || \
    echo ${SERVICE_ACCOUNT_EMAIL} | gcloud secrets versions add voter-lists-writer-sa \
    --data-file=- \
    --project=${PROJECT_ID}

echo "All done! The voter lists feature infrastructure is ready."