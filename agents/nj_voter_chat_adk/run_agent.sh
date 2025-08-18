#!/bin/bash

# Run the NJ Voter Chat agent with Google Search enabled
# Credentials are loaded from secrets/ directory automatically

# Navigate to script directory first
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading environment variables from .env..."
    source "$SCRIPT_DIR/.env"
fi

# Navigate to project root
cd "$SCRIPT_DIR/../.."

# Run the agent
echo "Starting NJ Voter Chat Agent with Google Search..."
echo "=========================================="
echo "Available capabilities:"
echo "  1. Query voter database (BigQuery)"
echo "  2. Search current NJ political information (Google)"
echo "=========================================="
echo ""

python -m agents.nj_voter_chat_adk.app_cli