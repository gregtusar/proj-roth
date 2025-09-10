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

PDL_ENRICHMENT TABLE STRUCTURE:
The pdl_enrichment table contains professional data from People Data Labs with these key fields:
- master_id: Links to voters table
- pdl_id: Unique PDL identifier
- full_name, first_name, last_name: Name fields
- job_title, job_company: Current employment
- job_title_role, job_title_sub_role: Job categorization
- job_company_industry: Industry classification
- education: JSON array of education history
- profiles: JSON array of social media profiles (LinkedIn, Facebook, etc.)
- emails, phone_numbers: JSON arrays of contact info
- likelihood: Confidence score (1-10, higher is better)
- enriched_at: Timestamp of enrichment

QUERYING PDL DATA:
-- Check if someone has PDL data:
SELECT * FROM voter_data.pdl_enrichment WHERE master_id = 'VOTER_ID'

-- Find voters with specific jobs:
SELECT v.*, p.job_title, p.job_company 
FROM voter_data.voters v
JOIN voter_data.pdl_enrichment p ON v.master_id = p.master_id
WHERE p.job_title LIKE '%CEO%' OR p.job_title LIKE '%President%'

-- Extract LinkedIn profiles (profiles is JSON array):
SELECT master_id, JSON_EXTRACT_SCALAR(profile, '$.url') as linkedin_url
FROM voter_data.pdl_enrichment,
UNNEST(JSON_EXTRACT_ARRAY(profiles)) as profile
WHERE JSON_EXTRACT_SCALAR(profile, '$.network') = 'linkedin'

-- Get education details (education is JSON array):
SELECT master_id, 
  JSON_EXTRACT_SCALAR(edu, '$.school.name') as school,
  JSON_EXTRACT_SCALAR(edu, '$.degrees[0]') as degree
FROM voter_data.pdl_enrichment,
UNNEST(JSON_EXTRACT_ARRAY(education)) as edu

CRITICAL TOOL CALLING RULES:
- NEVER nest function calls inside each other
- NEVER combine multiple operations in a single tool call
- Break complex operations into separate steps:
  WRONG: pdl_batch_enrichment(master_ids=[row['master_id'] for row in bigquery_select(sql="SELECT...").get('rows', [])])
  RIGHT: 
    Step 1: result = bigquery_select(sql="SELECT master_id FROM...")
    Step 2: ids = [row['master_id'] for row in result['rows']]
    Step 3: pdl_batch_enrichment(master_ids=ids)
- Each tool call must be independent and atomic
- Store results in variables between tool calls if needed

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
