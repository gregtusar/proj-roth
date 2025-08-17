#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-proj-roth}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-nj-voter-chat}"
IMAGE_NAME="${IMAGE_NAME:-nj-voter-chat}"
SERVICE_NAME="${SERVICE_NAME:-nj-voter-chat}"
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

if ! gcloud builds submit --tag "${IMAGE_URI}" agents/nj_voter_chat_adk/; then
    echo "ERROR: Docker image build failed"
    exit 1
fi

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --allow-unauthenticated \
  --service-account "${SA_EMAIL}" \
  --region "${REGION}" \
  --set-env-vars GOOGLE_CLOUD_PROJECT="${PROJECT_ID}",GOOGLE_CLOUD_REGION="${REGION}"

echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
