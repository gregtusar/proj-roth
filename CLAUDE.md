# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the NJ Voter Data Analysis Framework (proj-roth) - a Python-based system for analyzing New Jersey voter registration data with 622,000+ records from Congressional District 07. The project includes data analysis pipelines, geocoding services, and a conversational AI agent using Google's ADK (Agent Development Kit) with Gemini.

## Key Commands

### Development Setup
```bash
# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies for the ADK agent
pip install -r agents/nj_voter_chat_adk/requirements.txt

# Set required environment variables
export GOOGLE_CLOUD_PROJECT=proj-roth
export GOOGLE_CLOUD_REGION=us-central1
```

### Running the Agent
```bash
# CLI version (for testing only)
python -m agents.nj_voter_chat_adk.app_cli

# Main application (React frontend + Python backend)
python backend/main.py
# Then navigate to http://localhost:8080
```

### Testing
```bash
# Run unit tests for the agent
pytest agents/nj_voter_chat_adk/tests/

# Test specific functionality
python agents/nj_voter_chat_adk/test_integration.py
python agents/nj_voter_chat_adk/test_geocoding.py
python agents/nj_voter_chat_adk/test_search.py
```

### Deployment
```bash
# Deploy to Cloud Run (requires GCP permissions)
PROJECT_ID=proj-roth REGION=us-central1 bash scripts/deploy_nj_voter_chat.sh

# Test build locally
bash test_simple_build.sh
```

### Data Loading & Donation Matching Pipeline
```bash
# IMPORTANT: Use this script for donation-to-voter fuzzy matching
# This algorithm ignores ZIP codes due to corruption in source data
bq query --use_legacy_sql=false < scripts/fuzzy_match_no_zip.sql

# This script:
# - Matches donations to voter records using name + city/state (no ZIP)
# - Includes nickname resolution (GREG->GREGORY, MIKE->MICHAEL, etc.)  
# - Creates/replaces proj-roth.voter_data.donations table
# - Achieves ~24% match rate despite corrupted ZIP data
# Note: Source donations CSV has corrupted ZIPs (e.g., "79241106" instead of "07924")
```

## Architecture

### Data Layer (BigQuery)
- **Main tables**: `proj-roth.voter_data.voters` and `proj-roth.voter_data.street_party_summary`
- **Schema**: Defined in `config/bigquery_schema.sql` with 80+ fields including demographics, geography, voting history
- **Geospatial**: All voter records have GEOGRAPHY type location fields for spatial queries
- **Access**: Read-only access enforced through BigQueryReadOnlyTool with guardrails

### Agent Architecture (agents/nj_voter_chat_adk/)
- **agent.py**: Main ADK agent using Gemini, exposes four tools:
  - `bigquery_select`: Execute read-only SQL with automatic field mapping
  - `geocode_address`: Convert addresses to lat/lng via Google Maps
  - `google_search`: Search for current NJ political information
  - `save_voter_list`: Save query results for later use
- **bigquery_tool.py**: Implements SQL validation, table allowlisting, row limits (10K max)
- **config.py**: Central configuration for model, prompts, and constraints
- **app_cli.py**: CLI interface for testing the agent

### Data Processing Scripts (scripts/)
- **geocoding/**: Pipeline scripts for batch geocoding voter addresses using Google Maps API
- **analysis/**: Data analysis including demographics and voting patterns
- **visualization/**: Generate maps and charts from voter data
- **setup/**: Environment and BigQuery setup utilities

### Security & Guardrails
- SQL queries restricted to SELECT-only operations
- Table access limited to allowlisted tables (voters, street_party_summary)
- Maximum 10,000 rows per query, 60-second timeout
- Service account authentication with minimal permissions
- No write operations permitted on production data

## Important Context

### Congressional District Mapping
- All voters are in NJ Congressional District 07
- The BigQuery field `congressional_name` stores values as "NJ CONGRESSIONAL DISTRICT 07" (not "NJ-07")
- Counties included: Union, Somerset, Hunterdon, Morris, Warren, Essex, Sussex

### Field Name Mapping
The agent automatically maps common field names to actual schema:
- `voter_id` → `id`
- `party` → `demo_party` 
- `address` → `addr_residential_line1`
- `first_name` → `name_first`
- `last_name` → `name_last`

### Geospatial Queries
Use BigQuery's geography functions for spatial analysis:
- `ST_DWITHIN()` for proximity searches
- `ST_CENTROID()` for finding geographic centers
- `ST_DISTANCE()` for measuring distances between voters

### API Keys and Secrets
- Google Maps API key stored in Secret Manager as `google-maps-api-key`
- Google Search API credentials in `google-search-api-key` and `google-search-cx`
- Service account uses Application Default Credentials (ADC)