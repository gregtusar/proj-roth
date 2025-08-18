#!/bin/bash
set -ex

echo "===== TEST DEPLOY SCRIPT ====="
echo "Current directory: $(pwd)"

# Force absolute path
cd /Users/gregorytusar/proj-roth
echo "Changed to: $(pwd)"

# Check files exist
echo "Checking files:"
ls -la agents/nj_voter_chat_adk/requirements.txt
ls -la agents/nj_voter_chat_adk/Dockerfile

# Set up variables
PROJECT_ID="proj-roth"
REGION="us-central1"
REPO_NAME="nj-voter-chat"
IMAGE_NAME="nj-voter-chat"
TIMESTAMP=$(date +%s)
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:test-${TIMESTAMP}"

echo "Will build image: ${IMAGE_URI}"

# Create simple cloudbuild config
cat > /tmp/test_deploy_build.yaml <<'ENDCONFIG'
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: 
      - 'build'
      - '-t'
      - '${_IMAGE_URI}'
      - '-f'
      - 'agents/nj_voter_chat_adk/Dockerfile'
      - '.'
images:
  - '${_IMAGE_URI}'
ENDCONFIG

echo "Config created at /tmp/test_deploy_build.yaml"
cat /tmp/test_deploy_build.yaml

echo "Running gcloud builds submit from $(pwd)"
echo "Full command:"
echo "gcloud builds submit --config=/tmp/test_deploy_build.yaml --substitutions=\"_IMAGE_URI=${IMAGE_URI}\" /Users/gregorytusar/proj-roth"

# Run the build
gcloud builds submit \
    --config=/tmp/test_deploy_build.yaml \
    --substitutions="_IMAGE_URI=${IMAGE_URI}" \
    /Users/gregorytusar/proj-roth

echo "===== TEST COMPLETE ====="