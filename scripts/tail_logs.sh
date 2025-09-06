#!/bin/bash

# Script to tail Cloud Run logs for the NJ Voter Chat App
# Shows real-time logs with campaign and SendGrid related messages

PROJECT_ID="proj-roth"
SERVICE_NAME="nj-voter-chat-app"
REGION="us-central1"

echo "📋 Tailing logs for $SERVICE_NAME in $REGION..."
echo "================================="
echo "Filtering for campaign and email-related messages"
echo "Press Ctrl+C to stop"
echo ""

# Use gcloud run services logs tail for real-time streaming
gcloud beta run services logs tail $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID
