#!/bin/bash

# Setup script for creating Google Search API secrets
# This script helps you store API credentials securely

echo "========================================"
echo "Google Search API Secrets Setup"
echo "========================================"
echo ""
echo "This script will help you store your API credentials as secrets."
echo "Choose where to store the secrets:"
echo ""
echo "1. Local secrets folder (./secrets/)"
echo "2. User home directory (~/.secrets/)"
echo "3. System directory (/etc/secrets/) - requires sudo"
echo ""
read -p "Select option (1-3): " OPTION

case $OPTION in
    1)
        SECRET_DIR="$(dirname "$0")/secrets"
        ;;
    2)
        SECRET_DIR="$HOME/.secrets"
        ;;
    3)
        SECRET_DIR="/etc/secrets"
        NEED_SUDO=true
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Creating secrets directory: $SECRET_DIR"

# Create directory
if [ "$NEED_SUDO" = true ]; then
    sudo mkdir -p "$SECRET_DIR"
    sudo chmod 700 "$SECRET_DIR"
else
    mkdir -p "$SECRET_DIR"
    chmod 700 "$SECRET_DIR"
fi

# Get API Key
echo ""
echo "Enter your Google API Key:"
echo "  (Get it from: https://console.cloud.google.com/apis/credentials)"
read -s -p "API Key: " API_KEY
echo ""

# Get Search Engine ID
echo "Enter your Search Engine ID:"
echo "  (Get it from: https://programmablesearchengine.google.com/)"
read -p "Search Engine ID: " ENGINE_ID

# Validate inputs
if [ -z "$API_KEY" ] || [ -z "$ENGINE_ID" ]; then
    echo "❌ Error: Both API Key and Search Engine ID are required"
    exit 1
fi

# Write secrets
if [ "$NEED_SUDO" = true ]; then
    echo "$API_KEY" | sudo tee "$SECRET_DIR/api-key" > /dev/null
    echo "$ENGINE_ID" | sudo tee "$SECRET_DIR/search-engine-id" > /dev/null
    sudo chmod 600 "$SECRET_DIR/api-key"
    sudo chmod 600 "$SECRET_DIR/search-engine-id"
else
    echo "$API_KEY" > "$SECRET_DIR/api-key"
    echo "$ENGINE_ID" > "$SECRET_DIR/search-engine-id"
    chmod 600 "$SECRET_DIR/api-key"
    chmod 600 "$SECRET_DIR/search-engine-id"
fi

echo ""
echo "✅ Secrets created successfully!"
echo "   - API key stored in: $SECRET_DIR/api-key"
echo "   - Search Engine ID stored in: $SECRET_DIR/search-engine-id"
echo ""

# Test the configuration
echo "Testing configuration..."
python3 -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('$0'))))

from agents.nj_voter_chat_adk.google_search_tool import GoogleSearchTool

tool = GoogleSearchTool()
if tool.api_key and tool.search_engine_id:
    print('✅ Secrets loaded successfully!')
    print(f'   - API Key: {tool.api_key[:10]}...')
    print(f'   - Engine ID: {tool.search_engine_id}')
    
    # Try a test search
    result = tool.search('test', 1)
    if 'error' not in result or 'not configured' not in result.get('error', ''):
        print('✅ API test successful!')
    else:
        print('⚠️  API test failed:', result.get('error', 'Unknown error'))
else:
    print('❌ Failed to load secrets')
    print('   API Key loaded:', 'Yes' if tool.api_key else 'No')
    print('   Search Engine ID loaded:', 'Yes' if tool.search_engine_id else 'No')
" 2>/dev/null || echo "⚠️  Could not test configuration automatically"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "The Google Search tool will now automatically load credentials from:"
echo "  $SECRET_DIR/api-key"
echo "  $SECRET_DIR/search-engine-id"
echo ""
echo "To update credentials, run this script again or edit the files directly."