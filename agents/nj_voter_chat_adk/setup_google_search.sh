#!/bin/bash

# Setup script for Google Search API credentials
# Run this script after obtaining your API key and Search Engine ID

echo "========================================"
echo "Google Search API Setup for NJ Voter Chat"
echo "========================================"
echo ""

# Check if .env file exists
ENV_FILE="${HOME}/proj-roth/agents/nj_voter_chat_adk/.env"

# Prompt for API Key
echo "Step 1: Enter your Google API Key"
echo "  (Get it from: https://console.cloud.google.com/apis/credentials)"
read -p "API Key: " API_KEY

# Prompt for Search Engine ID
echo ""
echo "Step 2: Enter your Search Engine ID"
echo "  (Get it from: https://programmablesearchengine.google.com/)"
read -p "Search Engine ID: " ENGINE_ID

# Validate inputs
if [ -z "$API_KEY" ] || [ -z "$ENGINE_ID" ]; then
    echo "❌ Error: Both API Key and Search Engine ID are required"
    exit 1
fi

# Create or append to .env file
echo "" >> "$ENV_FILE"
echo "# Google Search API Configuration" >> "$ENV_FILE"
echo "export GOOGLE_SEARCH_API_KEY=\"$API_KEY\"" >> "$ENV_FILE"
echo "export GOOGLE_SEARCH_ENGINE_ID=\"$ENGINE_ID\"" >> "$ENV_FILE"
echo "export SEARCH_CACHE_TTL=3600" >> "$ENV_FILE"
echo "export SEARCH_MAX_RESULTS=5" >> "$ENV_FILE"
echo "export SEARCH_RATE_LIMIT=10" >> "$ENV_FILE"

echo ""
echo "✅ Configuration saved to $ENV_FILE"
echo ""

# Also export for current session
export GOOGLE_SEARCH_API_KEY="$API_KEY"
export GOOGLE_SEARCH_ENGINE_ID="$ENGINE_ID"

# Test the configuration
echo "Testing configuration..."
python3 -c "
import os
from agents.nj_voter_chat_adk.google_search_tool import GoogleSearchTool

tool = GoogleSearchTool()
result = tool.search('test query', 1)

if 'error' not in result or 'not configured' not in result.get('error', ''):
    print('✅ API configuration is valid!')
    print(f'   - API Key: {os.getenv(\"GOOGLE_SEARCH_API_KEY\")[:10]}...')
    print(f'   - Engine ID: {os.getenv(\"GOOGLE_SEARCH_ENGINE_ID\")[:10]}...')
else:
    print('⚠️  Configuration may have issues. Error:', result.get('error', 'Unknown'))
" 2>/dev/null || echo "⚠️  Could not test configuration automatically"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To use these credentials in future sessions, add this to your shell profile:"
echo "  source $ENV_FILE"
echo ""
echo "Or run this command now:"
echo "  source $ENV_FILE"
echo ""
echo "Then test with:"
echo "  python agents/nj_voter_chat_adk/test_search.py"