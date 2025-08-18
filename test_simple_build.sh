#!/bin/bash
set -ex

# Make absolutely sure we're in the project root
cd /Users/gregorytusar/proj-roth
echo "Current directory: $(pwd)"
echo "Listing agents directory:"
ls -la agents/nj_voter_chat_adk/ | head -5

# Simple build with explicit config
IMAGE="us-central1-docker.pkg.dev/proj-roth/nj-voter-chat/nj-voter-chat:test-$(date +%s)"

cat > /tmp/simple_cloudbuild.yaml <<'EOF'
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${_IMAGE}', '-f', 'agents/nj_voter_chat_adk/Dockerfile', '.']
images: ['${_IMAGE}']
EOF

echo "Config file:"
cat /tmp/simple_cloudbuild.yaml

echo "Building with:"
echo "  Config: /tmp/simple_cloudbuild.yaml"
echo "  Image: $IMAGE"
echo "  Source: $(pwd)"

gcloud builds submit \
    --config=/tmp/simple_cloudbuild.yaml \
    --substitutions="_IMAGE=$IMAGE" \
    /Users/gregorytusar/proj-roth