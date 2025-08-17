import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
DATASET = os.getenv("VOTER_DATASET", "voter_data")
ALLOWED_TABLES = {
    f"{PROJECT_ID}.{DATASET}.voters",
    f"{PROJECT_ID}.{DATASET}.street_party_summary",
}
MAX_ROWS = int(os.getenv("BQ_MAX_ROWS", "10000"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("BQ_QUERY_TIMEOUT_SECONDS", "60"))
MODEL = os.getenv("ADK_MODEL", "gemini-2.5-pro")
SYSTEM_PROMPT = os.getenv(
    "ADK_SYSTEM_PROMPT",
    """You are a data assistant for NJ voter data with two powerful capabilities:

1. DATABASE QUERIES (bigquery_select): Query voter data from BigQuery tables
   - voter_data.voters: Individual voter records with demographics and voting history
   - voter_data.street_party_summary: Aggregated party data by street
   - Only run read-only SELECT queries
   - demo_party values are exactly: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED' (case-sensitive)

2. WEB SEARCH (google_search): Find current information about NJ politics and elections
   - Recent election results and news
   - Information about candidates and elected officials
   - Voting locations and procedures
   - Political events and developments in NJ
   - Use this when asked about current events or information not in the database

COMBINING TOOLS:
- When asked about a candidate: Search for current info, then query voter patterns in their district
- When asked about recent elections: Search for results, then analyze historical voting data
- When asked about trends: Query historical data, then search for recent news and analysis

Always choose the most appropriate tool(s) for the question. Use both when it adds value.""",
)
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")

# Google Search API Configuration
# API credentials are loaded from secrets by GoogleSearchTool
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", "3600"))  # 1 hour default
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
SEARCH_RATE_LIMIT = int(os.getenv("SEARCH_RATE_LIMIT", "10"))  # per minute
