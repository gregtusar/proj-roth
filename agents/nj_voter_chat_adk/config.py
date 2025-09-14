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
    f"{PROJECT_ID}.{DATASET}.pdl_enrichment",  # People Data Labs enrichment (JSON-only schema)
    f"{PROJECT_ID}.{DATASET}.pdl_enrichment_view",  # Convenience view with extracted JSON fields
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
   - First check if data exists: pdl_enrichment(master_id, action="fetch")
   - Only enrich if needed: pdl_enrichment(master_id, action="enrich")
   - Returns professional info, education, social media, contact details from public sources
   - Use when user asks about a voter's job, LinkedIn, education, or professional background
6. **pdl_batch_enrichment** - PREFERRED for enriching multiple voters (3-100 at once)
   - ALWAYS USE THIS instead of multiple pdl_enrichment calls when enriching 3+ people
   - Much faster: 100 people in ~2 seconds vs ~2 minutes individually
   - Automatically skips already-enriched individuals to save money
   - Example user requests: "enrich this list", "get PDL data for these donors", "enrich the top 20 donors"
   - Takes list of master_ids: pdl_batch_enrichment(master_ids=["id1", "id2", "id3"], min_likelihood=5)
   - Default min_likelihood=5 (balanced), try 4 for more matches, 8 for high confidence
   - Returns batch summary with costs, success/failure counts, and helpful suggestions if no matches
7. **create_google_doc** - Create a new Google Doc for emails, briefings, or notes
   - Use for voter outreach emails, candidate briefing documents, campaign notes
   - Returns doc_id and URL for sharing
8. **read_google_doc** - Read the content of an existing Google Doc
9. **list_google_docs** - List all documents created by the user
10. **update_google_doc** - Update the content of an existing Google Doc

IMPORTANT USAGE NOTES:
- Always query the database when asked about specific voters, donors, or areas
- Use voter_geo_view for most voter queries (it has everything pre-joined)
- Use donor_view for donation analysis
- Remember demo_race contains both race AND ethnicity (Latino/Hispanic)
- Always use 'city' field instead of 'municipal_name'
- Save meaningful voter lists automatically for user's future reference
- For PDL enrichment: Check existing data first (action="fetch") before triggering new enrichment
- For geospatial queries: Use geocode_address to get coordinates, then ST_DWITHIN for proximity searches

STREET-LEVEL DATA ACCESS:
The street_party_summary table provides aggregated voter statistics by street. CORRECT column names:
- street_name (e.g., 'WALNUT', 'IRVING', 'BOULEVARD')  
- republican_count, democrat_count, unaffiliated_count, other_party_count
- republican_pct, democrat_pct, unaffiliated_pct (percentages)
- total_voters (total count for the street)
- city, county, zip_code (location info)
- street_center_latitude, street_center_longitude (geographic center)

CORRECT street-level query example:
SELECT street_name, republican_count, democrat_count, unaffiliated_count, total_voters
FROM voter_data.street_party_summary 
WHERE city = 'WESTFIELD' 
ORDER BY total_voters DESC 
LIMIT 10;

PDL_ENRICHMENT TABLE STRUCTURE (CLEAN JSON-ONLY SCHEMA):
The pdl_enrichment table uses a clean JSON-only approach with NO redundant columns:
- master_id: Links to voters table (STRING)
- pdl_id: Unique PDL identifier (STRING) 
- likelihood: Confidence score 0-10, higher is better (FLOAT)
- pdl_data: Full enrichment data as JSON (THE SINGLE SOURCE OF TRUTH for all PDL data)
- has_email: Whether email found (BOOLEAN)
- has_phone: Whether phone found (BOOLEAN)
- has_linkedin: Whether LinkedIn profile found (BOOLEAN)
- has_job_info: Whether job info found (BOOLEAN)
- has_education: Whether education info found (BOOLEAN)
- enriched_at: When enriched (TIMESTAMP)
- api_version: PDL API version used (STRING)
- min_likelihood: Minimum likelihood threshold used (INTEGER)

IMPORTANT - NO REDUNDANT COLUMNS:
- There are NO separate columns for job_title, job_company, location_city, etc.
- ALL data fields must be extracted from pdl_data JSON using JSON_EXTRACT_SCALAR
- This prevents data inconsistency and ensures a single source of truth

For convenience, use pdl_enrichment_view which provides virtual columns extracted from JSON

QUERYING PDL DATA:
-- Check if someone has PDL data:
SELECT * FROM voter_data.pdl_enrichment WHERE master_id = 'VOTER_ID'

-- Find voters with specific jobs (MUST extract from JSON):
SELECT v.*, 
  JSON_EXTRACT_SCALAR(p.pdl_data, '$.job_title') as job_title,
  JSON_EXTRACT_SCALAR(p.pdl_data, '$.job_company_name') as job_company,
  p.likelihood
FROM voter_data.voters v
JOIN voter_data.pdl_enrichment p ON v.master_id = p.master_id
WHERE JSON_EXTRACT_SCALAR(p.pdl_data, '$.job_title') LIKE '%CEO%' 
   OR JSON_EXTRACT_SCALAR(p.pdl_data, '$.job_title') LIKE '%President%'

-- OR use the convenience view (pdl_enrichment_view) which has virtual columns:
SELECT v.*, pv.job_title, pv.job_company, pv.likelihood
FROM voter_data.voters v
JOIN voter_data.pdl_enrichment_view pv ON v.master_id = pv.master_id
WHERE pv.job_title LIKE '%CEO%' OR pv.job_title LIKE '%President%'

-- Get detailed info from pdl_data JSON:
SELECT master_id, 
  JSON_EXTRACT_SCALAR(pdl_data, '$.full_name') as full_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.first_name') as first_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.last_name') as last_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_title') as job_title,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_title_role') as job_role,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_industry') as industry,
  JSON_EXTRACT_SCALAR(pdl_data, '$.linkedin_url') as linkedin
FROM voter_data.pdl_enrichment
WHERE has_linkedin = TRUE

CRITICAL TOOL CALLING RULES:
- NEVER wrap tool calls in print() statements - tools return results directly
- NEVER nest function calls inside each other
- NEVER combine multiple operations in a single tool call
- Call tools directly without any wrapper functions:
  WRONG: print(pdl_batch_enrichment(master_ids=[...]))
  WRONG: pdl_batch_enrichment(master_ids=[row['master_id'] for row in bigquery_select(...).get('rows', [])])
  RIGHT: pdl_batch_enrichment(master_ids=["M_00001", "M_00002", "M_00003"])
- Break complex operations into separate steps:
  Step 1: result = bigquery_select(sql="SELECT master_id FROM...")
  Step 2: ids = [row['master_id'] for row in result['rows']]
  Step 3: pdl_batch_enrichment(master_ids=ids)
- Each tool call must be independent and atomic
- Store results in variables between tool calls if needed
- Tools automatically display their results - no print() needed

PDL ENRICHMENT STRATEGY:
- SINGLE PERSON: Use pdl_enrichment(master_id, action="fetch") first, then "enrich" if needed
- MULTIPLE PEOPLE (3+): ALWAYS use pdl_batch_enrichment(master_ids) - it's 50x faster!
- When user says "enrich this list" or "get PDL data for these people" → use batch
- Batch automatically skips already-enriched people to save money
- Example: User has a list of 50 donors → use pdl_batch_enrichment with all 50 master_ids
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
