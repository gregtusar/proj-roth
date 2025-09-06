#!/bin/bash

# Tail Cloud Run logs for nj-voter-chat-app
# This script continuously polls for new logs every 2 seconds

PROJECT_ID="proj-roth"
SERVICE_NAME="nj-voter-chat-app"
POLL_INTERVAL=2

echo "Tailing logs for Cloud Run service: $SERVICE_NAME"
echo "Project: $PROJECT_ID"
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

# Track the last timestamp to avoid duplicates
LAST_TIMESTAMP=""

while true; do
    # Get logs from the last 10 seconds
    LOGS=$(gcloud logging read \
        "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND timestamp>=\"$(date -u -v-10S '+%Y-%m-%dT%H:%M:%S')\"" \
        --project=$PROJECT_ID \
        --format="csv[no-heading](timestamp,severity,textPayload)" \
        --limit=100 \
        2>/dev/null)
    
    if [ ! -z "$LOGS" ]; then
        # Process and display new logs
        while IFS= read -r line; do
            TIMESTAMP=$(echo "$line" | cut -d',' -f1)
            if [ "$TIMESTAMP" != "$LAST_TIMESTAMP" ] && [ ! -z "$TIMESTAMP" ]; then
                echo "$line" | sed 's/,/ | /g'
                LAST_TIMESTAMP="$TIMESTAMP"
            fi
        done <<< "$LOGS"
    fi
    
    sleep $POLL_INTERVAL
done