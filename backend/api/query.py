from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from google.cloud import bigquery
from api.auth import get_current_user
from core.config import settings
import google.generativeai as genai
from google.cloud import secretmanager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize BigQuery client
client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)

# Load Gemini API key from Secret Manager
def get_gemini_api_key():
    """Load Gemini API key from Google Secret Manager"""
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{settings.GOOGLE_CLOUD_PROJECT}/secrets/api-key/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.warning(f"Could not load Gemini API key from Secret Manager: {e}")
        # Fallback to environment variable if available
        import os
        return os.getenv('GOOGLE_API_KEY')

# Initialize Gemini
api_key = get_gemini_api_key()
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.error("No Gemini API key found")
    model = None

class GenerateSQLRequest(BaseModel):
    prompt: str

class GenerateSQLResponse(BaseModel):
    sql: str
    prompt: str

class ExecuteQueryRequest(BaseModel):
    sql: str

class QueryResult(BaseModel):
    rows: List[Dict[str, Any]]
    totalCount: Optional[int] = None

# Import database manifest and schema
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.database_manifest import format_for_llm
    DATABASE_CONTEXT = format_for_llm()
except ImportError:
    DATABASE_CONTEXT = ""

# Import centralized schema as fallback
try:
    from core.voter_schema import SYSTEM_PROMPT_CACHED as SCHEMA_PROMPT
except ImportError:
    SCHEMA_PROMPT = ""

# Build comprehensive SQL generation prompt
SYSTEM_PROMPT = f"""You are a SQL expert for New Jersey voter data analysis in Congressional District 07.

{DATABASE_CONTEXT}

CRITICAL SQL GENERATION RULES:
1. ALWAYS scope table names with 'voter_data.' prefix (e.g., 'voter_data.voters' not just 'voters')
2. Generate only SELECT queries - no INSERT, UPDATE, DELETE, CREATE, etc.
3. Use the recommended views (voter_geo_view, donor_view) whenever possible - they have everything pre-joined
4. Do NOT add LIMIT clauses unless the user explicitly requests limiting results
5. Party values must be EXACT CASE: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED' (not 'Republican' or 'democrat')
6. Congressional district is stored as 'NJ CONGRESSIONAL DISTRICT 07' not 'NJ-07'
7. Use ST_* functions for all spatial/geographic queries with meters (1 mile = 1609.34 meters)
8. The geography field in addresses table is 'geo_location' NOT 'geo' 
9. To link individuals to addresses: JOIN through individual_addresses table
10. demo_race field contains BOTH race AND ethnicity (Latino/Hispanic are here, not separate)
11. Always use 'city' field instead of 'municipal_name' (which has many NULLs)
12. Names are in 'LASTNAME, FIRSTNAME' format in standardized_name field
13. For donation searches, check both matched (master_id NOT NULL) and unmatched records
14. Cities and counties are UPPERCASE in the database ('SUMMIT' not 'Summit')

COMMON QUERY PATTERNS:
- Find voters by name: Use voter_geo_view with standardized_name LIKE pattern
- Find donors by location: Join donations->individuals->individual_addresses->addresses using geo_location field
- Find Latino voters: demo_race LIKE '%LATINO%' OR demo_race LIKE '%HISPANIC%'
- Spatial queries: ST_DWITHIN(geo_location, ST_GEOGPOINT(lng, lat), distance_in_meters)

Generate clean SQL without markdown formatting or explanations.
{SCHEMA_PROMPT if not DATABASE_CONTEXT else ''}"""

@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest, current_user: dict = Depends(get_current_user)):
    """Generate SQL from natural language prompt using Gemini"""
    if not model:
        raise HTTPException(status_code=503, detail="SQL generation service is not available")
    
    try:
        # Generate SQL using Gemini
        prompt = f"{SYSTEM_PROMPT}\n\nUser request: {request.prompt}\n\nSQL:"
        response = model.generate_content(prompt)
        
        # Clean up the SQL
        sql = response.text.strip()
        # Remove markdown code blocks if present
        if sql.startswith('```'):
            sql = sql.split('```')[1]
            if sql.startswith('sql'):
                sql = sql[3:]
        sql = sql.strip()
        
        # Ensure it's a SELECT query
        if not sql.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        return GenerateSQLResponse(sql=sql, prompt=request.prompt)
        
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")

@router.post("/execute-query", response_model=QueryResult)
async def execute_query(request: ExecuteQueryRequest, current_user: dict = Depends(get_current_user)):
    """Execute a BigQuery SQL query"""
    try:
        # Basic validation - ensure it's a SELECT query
        sql = request.sql.strip()
        if not sql.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Check for dangerous keywords
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        # Execute query
        query_job = client.query(sql)
        results = query_job.result(timeout=30)
        
        # Convert results to list of dicts
        rows = []
        for row in results:
            row_dict = {}
            for key, value in row.items():
                # Handle special types
                if hasattr(value, 'isoformat'):  # datetime
                    row_dict[key] = value.isoformat()
                elif hasattr(value, '__geo_interface__'):  # geography
                    row_dict[key] = str(value)
                else:
                    row_dict[key] = value
            rows.append(row_dict)
        
        return QueryResult(rows=rows)
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")