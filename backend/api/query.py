from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from api.auth import get_current_user
from core.config import settings
import google.generativeai as genai
from google.cloud import secretmanager
from services.bigquery_service import execute_query as execute_bq_query

logger = logging.getLogger(__name__)
router = APIRouter()

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
# All database knowledge is now centralized in database_manifest.py
SYSTEM_PROMPT = f"""You are a SQL expert for New Jersey voter data analysis in Congressional District 07.

{DATABASE_CONTEXT}

ADDITIONAL RULES FOR SQL GENERATION:
- Generate only SELECT queries - no INSERT, UPDATE, DELETE, CREATE, etc.
- Do NOT add LIMIT clauses unless the user explicitly requests limiting results
- Generate clean SQL without markdown formatting or explanations
- Follow all the rules and examples provided in the database manifest above

When generating SQL, pay special attention to:
- The CRITICAL SQL GENERATION RULES section
- The QUERY PATTERNS WITH SQL EXAMPLES section  
- The FINAL REMINDERS section

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

@router.post("/execute-query")
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
        
        # Execute query using the bigquery service (returns full dataset)
        # Pass limit=0 to not add any LIMIT clause
        result = await execute_bq_query(sql, limit=0)
        return result
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")