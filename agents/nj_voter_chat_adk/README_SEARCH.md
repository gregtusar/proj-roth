# Google Search Integration for NJ Voter Chat Agent

## Overview
The NJ Voter Chat agent now has Google Search capability in addition to BigQuery database queries.

## Configuration

Credentials are stored securely as secrets in the `secrets/` directory:
- `secrets/api-key` - Google API Key
- `secrets/search-engine-id` - Search Engine ID

### Setting Up Secrets

Run the setup script to configure your secrets:
```bash
./setup_secrets.sh
```

Or manually create the files:
```bash
mkdir -p secrets
echo "your-api-key" > secrets/api-key
echo "your-search-engine-id" > secrets/search-engine-id
chmod 600 secrets/*
```

The tool will automatically look for secrets in these locations:
1. `./secrets/` (local directory)
2. `~/.secrets/` (user home)
3. `/etc/secrets/` (system-wide)
4. `/run/secrets/` (Docker/Kubernetes)

## Usage

### Running the Agent
```bash
# From the agent directory
./run_agent.sh

# Or manually
source .env
python -m agents.nj_voter_chat_adk.app_cli
```

### Example Queries
The agent can now answer questions like:
- "Who is the current governor of NJ?"
- "What are the latest election results in Bergen County?"
- "Find information about NJ Senate candidates"
- "Show me Democrats on Main Street and recent news about the district"

### Testing
```bash
# Test search functionality
python test_search.py

# Test full integration
python test_integration.py
```

## Features
- **Automatic NJ Context**: Adds "New Jersey" to searches when not present
- **Caching**: Results cached for 1 hour to reduce API calls
- **Rate Limiting**: Maximum 10 searches per minute
- **Error Handling**: Graceful fallback if search fails

## API Limits
- **Free Tier**: 100 searches per day
- **Paid Tier**: $5 per 1000 queries (if needed)

## Tools Available
1. **bigquery_select**: Query voter database
2. **google_search**: Search current information

The agent will automatically choose the appropriate tool(s) based on your question.