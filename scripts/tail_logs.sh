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

# Function to fetch and display logs
fetch_logs() {
    gcloud logging read \
      "resource.type=cloud_run_revision AND \
       resource.labels.service_name=$SERVICE_NAME AND \
       resource.labels.location=$REGION AND \
       (textPayload:\"CAMPAIGN\" OR \
        textPayload:\"SENDGRID\" OR \
        textPayload:\"EMAIL\" OR \
        textPayload:\"campaign\" OR \
        textPayload:\"send_campaign\" OR \
        textPayload:\"get_list_recipients\" OR \
        textPayload:\"403\" OR \
        textPayload:\"400\" OR \
        textPayload:\"Permission\" OR \
        textPayload:\"Google Docs\")" \
      --project=$PROJECT_ID \
      --format="table(timestamp,textPayload)" \
      --order=desc \
      --limit=20
}

# Tail logs continuously
while true; do
    clear
    echo "📋 Campaign/Email Logs - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================="
    fetch_logs
    echo ""
    echo "Refreshing in 5 seconds... (Press Ctrl+C to stop)"
    sleep 5
done
