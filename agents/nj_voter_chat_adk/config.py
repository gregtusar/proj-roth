import os
import sys
from pathlib import Path

# Import database manifest
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.database_manifest import DATABASE_MANIFEST, format_for_llm
    DATABASE_CONTEXT = format_for_llm()
except ImportError:
    DATABASE_CONTEXT = "Database manifest not available"
    DATABASE_MANIFEST = {}

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
DATASET = os.getenv("VOTER_DATASET", "voter_data")

# Extract allowed tables from manifest
ALLOWED_TABLES = {
    # Core tables from manifest
    f"{PROJECT_ID}.{DATASET}.voters",
    f"{PROJECT_ID}.{DATASET}.individuals",
    f"{PROJECT_ID}.{DATASET}.addresses",
    f"{PROJECT_ID}.{DATASET}.individual_addresses",
    f"{PROJECT_ID}.{DATASET}.donations",
    f"{PROJECT_ID}.{DATASET}.street_party_summary",
    f"{PROJECT_ID}.{DATASET}.pdl_enrichment",  # People Data Labs enrichment
    # Raw data tables
    f"{PROJECT_ID}.{DATASET}.raw_voters",
    f"{PROJECT_ID}.{DATASET}.raw_donations",
    # Views from manifest
    f"{PROJECT_ID}.{DATASET}.voter_geo_view",
    f"{PROJECT_ID}.{DATASET}.donor_view",
    f"{PROJECT_ID}.{DATASET}.high_frequency_voters",
    f"{PROJECT_ID}.{DATASET}.major_donors",
    f"{PROJECT_ID}.{DATASET}.voter_donor_mv",
    f"{PROJECT_ID}.{DATASET}.voter_geo_summary_mv",
    # Additional views for compatibility
    f"{PROJECT_ID}.{DATASET}.street_party_summary_new",
    f"{PROJECT_ID}.{DATASET}.voters_compat",
}

MAX_ROWS = int(os.getenv("BQ_MAX_ROWS", "1000000"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("BQ_QUERY_TIMEOUT_SECONDS", "600"))
MODEL = os.getenv("ADK_MODEL", "gemini-2.5-pro")
MAX_OUTPUT_TOKENS = int(os.getenv("ADK_MAX_OUTPUT_TOKENS", "32768"))

# Build system prompt with database manifest
base_prompt = """
You have access to comprehensive voter data and current political information via the following tools:

{database_context}

AVAILABLE TOOLS:
1. **bigquery_select** - Execute read-only SQL queries against voter and donor databases
2. **geocode_address** - Convert addresses to coordinates for spatial queries
   - Use this to find lat/lng for locations like "Summit train station" or "123 Main St"
   - Then use ST_DWITHIN(location, ST_GEOGPOINT(lng, lat), meters) to find nearby voters
   - Example: Find all voters within 500m of an address or landmark
3. **google_search** - Search for current NJ political information
4. **save_voter_list** - Save query results for later use in List Manager
5. **pdl_enrichment** - Fetch or trigger People Data Labs enrichment for individual voters
   - IMPORTANT: Costs $0.25 per enrichment! Use sparingly for high-value voters only
   - First check if data exists: pdl_enrichment(master_id, action="fetch")
   - Only enrich if needed: pdl_enrichment(master_id, action="enrich")
   - Returns professional info, education, social media, contact details from public sources
   - Use when user asks about a voter's job, LinkedIn, education, or professional background
6. **create_google_doc** - Create a new Google Doc for emails, briefings, or notes
   - Use for voter outreach emails, candidate briefing documents, campaign notes
   - Returns doc_id and URL for sharing
7. **read_google_doc** - Read the content of an existing Google Doc
8. **list_google_docs** - List all documents created by the user
9. **update_google_doc** - Update the content of an existing Google Doc

IMPORTANT USAGE NOTES:
- Always query the database when asked about specific voters, donors, or areas
- Use voter_geo_view for most voter queries (it has everything pre-joined)
- Use donor_view for donation analysis
- Remember demo_race contains both race AND ethnicity (Latino/Hispanic)
- Always use 'city' field instead of 'municipal_name'
- Save meaningful voter lists automatically for user's future reference
- For PDL enrichment: Check existing data first (action="fetch") before triggering new enrichment
- For geospatial queries: Use geocode_address to get coordinates, then ST_DWITHIN for proximity searches
"""

# Format the system prompt with database manifest
SYSTEM_PROMPT = os.getenv(
    "ADK_SYSTEM_PROMPT",
    base_prompt.format(database_context=DATABASE_CONTEXT)
)

BQ_LOCATION = os.getenv("BQ_LOCATION", "US")

# Google Search API Configuration
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", "3600"))  # 1 hour default
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
SEARCH_RATE_LIMIT = int(os.getenv("SEARCH_RATE_LIMIT", "10"))  # per minute
