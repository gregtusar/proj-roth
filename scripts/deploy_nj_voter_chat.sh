#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-proj-roth}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-nj-voter-chat-app}"
IMAGE_NAME="${IMAGE_NAME:-nj-voter-chat-app}"
SERVICE_NAME="${SERVICE_NAME:-nj-voter-chat-app}"
SA_EMAIL="${SA_EMAIL:-agent-runner@${PROJECT_ID}.iam.gserviceaccount.com}"

gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="NJ Voter Chat images"
fi

gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q

COMMIT_HASH=$(git rev-parse --short HEAD)
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${COMMIT_HASH}-$(date +%s)"

# Create a temporary cloudbuild.yaml that uses the correct Dockerfile
cat > /tmp/cloudbuild_nj_voter.yaml <<EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${IMAGE_URI}', '-f', 'Dockerfile', '.']
images: ['${IMAGE_URI}']
EOF

if ! gcloud builds submit --config=/tmp/cloudbuild_nj_voter.yaml .; then
    echo "ERROR: Docker image build failed"
    exit 1
fi

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --allow-unauthenticated \
  --service-account "${SA_EMAIL}" \
  --region "${REGION}" \
  --set-env-vars GOOGLE_CLOUD_PROJECT="${PROJECT_ID}",GOOGLE_CLOUD_REGION="${REGION}",ADK_MAX_OUTPUT_TOKENS="32768" \
  --set-secrets="GOOGLE_CLIENT_ID=google-oauth-client-id:latest,GOOGLE_CLIENT_SECRET=google-oauth-client-secret:latest"

echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
