#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${PROJECT_ID:-proj-roth}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-nj-voter-chat-app}"
SA_EMAIL="${SA_EMAIL:-agent-runner@${PROJECT_ID}.iam.gserviceaccount.com}"
IMAGE_URI="us-central1-docker.pkg.dev/proj-roth/nj-voter-chat/nj-voter-chat-app:latest"

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --allow-unauthenticated \
  --service-account "${SA_EMAIL}" \
  --region "${REGION}" \
  --memory "2Gi" \
  --cpu "2" \
  --timeout "3600" \
  --max-instances "10" \
  --port "8080" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},DEBUG=False"

# Get the service URL
echo "✅ Deployment complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"