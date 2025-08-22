#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${PROJECT_ID:-proj-roth}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-nj-voter-chat}"
IMAGE_NAME="${IMAGE_NAME:-nj-voter-chat-app}"
SERVICE_NAME="${SERVICE_NAME:-nj-voter-chat-app}"
SA_EMAIL="${SA_EMAIL:-agent-runner@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "🚀 Starting deployment of NJ Voter Chat React App..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Set gcloud configuration
gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

# Create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  echo "📚 Creating Artifact Registry repository..."
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="NJ Voter Chat application images"
fi

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q

# Build and tag the image
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%s)
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${COMMIT_HASH}-${TIMESTAMP}"
LATEST_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

echo "🔨 Building Docker image..."
echo "Image URI: ${IMAGE_URI}"

# Submit build to Cloud Build
gcloud builds submit . \
  --tag="${IMAGE_URI}" \
  --timeout=30m

# Tag as latest
gcloud artifacts docker tags add "${IMAGE_URI}" "${LATEST_URI}"

# Deploy to Cloud Run
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
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}" \
  --set-env-vars "REACT_APP_API_URL=https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app"

# Get the service URL
echo "✅ Deployment complete!"
echo "Service URL:"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')
echo "${SERVICE_URL}"

# Update traffic to 100% on the latest revision
echo "🔄 Updating traffic to latest revision..."
gcloud run services update-traffic "${SERVICE_NAME}" --to-latest --region "${REGION}"

echo "🎉 Deployment successful!"
echo "Access your application at: ${SERVICE_URL}"