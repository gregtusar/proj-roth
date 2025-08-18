#!/bin/bash
set -x  # Enable debug output

# Set variables like the script does
PROJECT_ID="proj-roth"
REGION="us-central1"
REPO_NAME="nj-voter-chat"
IMAGE_NAME="nj-voter-chat"
ENVIRONMENT="test"

# Create image URIs
commit_hash=$(git rev-parse --short HEAD)
unique_image_uri="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:test-${commit_hash}"
image_uri="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
tagged_image_uri="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

# Create temporary cloudbuild config
temp_config="/tmp/test_cloudbuild_$$.yaml"
cat > "${temp_config}" <<EOF
steps:
  # Debug: Check what files are present
  - name: 'ubuntu'
    entrypoint: 'bash'
    args: 
      - '-c'
      - |
        echo "=== Current directory ==="
        pwd
        echo "=== Checking for requirements.txt ==="
        ls -la agents/nj_voter_chat_adk/requirements.txt || echo "NOT FOUND"
        echo "=== Checking agents directory ==="
        ls -la agents/ || echo "agents/ NOT FOUND"
        echo "=== Checking nj_voter_chat_adk directory ==="
        ls -la agents/nj_voter_chat_adk/ || echo "nj_voter_chat_adk/ NOT FOUND"
  
  # Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: 
      - 'build'
      - '-t'
      - '${unique_image_uri}'
      - '-f'
      - 'agents/nj_voter_chat_adk/Dockerfile'
      - '.'
images:
  - '${unique_image_uri}'
EOF

echo "Created config file: ${temp_config}"
cat "${temp_config}"

echo ""
echo "Running build with this config..."
gcloud builds submit \
    --config="${temp_config}" \
    . \
    --timeout=600