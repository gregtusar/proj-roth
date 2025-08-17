# Google Search Integration for NJ Voter Chat Agent

## Overview
The NJ Voter Chat agent now has Google Search capability in addition to BigQuery database queries.

## Configuration

The following credentials are configured in `.env`:
- **API Key**: `AIzaSyAgF90DnYRfBlTAppH3Unv2vK5yrav5Pzw`
- **Search Engine ID**: `91907e5365c574113`

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