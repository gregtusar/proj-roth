from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Literal
import logging
import google.generativeai as genai
from google.cloud import secretmanager
from api.auth import get_current_user
from core.config import settings
from services.bigquery_service import execute_query

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

class VisualizeRequest(BaseModel):
    prompt: str

class VisualizationResponse(BaseModel):
    type: Literal['voters', 'streets']
    data: List[Dict[str, Any]]
    query: str
    description: str
    total_count: int
    center_lat: float
    center_lon: float

# Import database context
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.database_manifest import format_for_llm
    DATABASE_CONTEXT = format_for_llm()
except ImportError:
    DATABASE_CONTEXT = ""

VISUALIZATION_PROMPT = f"""You are a SQL expert for New Jersey voter data visualization in Congressional District 07.

{DATABASE_CONTEXT}

VISUALIZATION RULES:
1. Analyze the user's request to determine if they want to visualize:
   - Individual voters (return type: "voters")
   - Streets/areas (return type: "streets")

2. For INDIVIDUAL VOTERS queries:
   - Must include: id, name_first || ' ' || name_last AS name, demo_party AS party, city, county, location (geography field)
   - Include ST_X(location) AS longitude and ST_Y(location) AS latitude
   - Do NOT add a LIMIT clause - return all matching results
   - Focus on specific criteria (party, city, voting history, etc.)

3. For STREETS queries:
   - Query from proj-roth.voter_data.street_party_summary table
   - Must include: street_name, city, county, republican_count, democrat_count, unaffiliated_count, 
     total_voters, republican_pct, democrat_pct, ST_X(location) AS longitude, ST_Y(location) AS latitude
   - Can include all streets or filter by criteria
   - Default minimum voters: 5

4. ALWAYS include proper geographic fields for mapping:
   - Use ST_X(location) AS longitude, ST_Y(location) AS latitude
   - Never return raw geography objects

5. Generate clean SQL without markdown formatting

OUTPUT FORMAT:
Return a JSON object with:
- type: "voters" or "streets"
- sql: The SQL query
- description: Human-readable description of what's being visualized

Examples:
User: "Show all Democratic voters in Westfield"
Output: {{
  "type": "voters",
  "sql": "SELECT id, name_first || ' ' || name_last AS name, demo_party AS party, city, county, ST_X(location) AS longitude, ST_Y(location) AS latitude FROM `proj-roth.voter_data.voters` WHERE city = 'WESTFIELD' AND demo_party = 'DEM'",
  "description": "Democratic voters in Westfield"
}}

User: "Show streets with high Republican concentration"
Output: {{
  "type": "streets",
  "sql": "SELECT street_name, city, county, republican_count, democrat_count, unaffiliated_count, total_voters, republican_pct, democrat_pct, ST_X(location) AS longitude, ST_Y(location) AS latitude FROM `proj-roth.voter_data.street_party_summary` WHERE republican_pct > 60 AND total_voters >= 10",
  "description": "Streets with high Republican concentration (>60%)"
}}"""

@router.post("/visualize", response_model=VisualizationResponse)
async def generate_visualization(
    request: VisualizeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate and execute a visualization query from natural language"""
    
    if not model:
        raise HTTPException(status_code=503, detail="Visualization service is not available")
    
    try:
        # Generate SQL and determine visualization type using Gemini
        prompt = f"""{VISUALIZATION_PROMPT}

User request: {request.prompt}

Output JSON:"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse the JSON response
        import json
        
        # Clean up response if needed
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("Failed to parse AI response as JSON")
        
        viz_type = result.get('type', 'voters')
        sql = result.get('sql', '')
        description = result.get('description', request.prompt)
        
        # Validate SQL
        if not sql.strip().upper().startswith('SELECT'):
            raise ValueError("Invalid SQL query generated")
        
        # Execute the query
        query_result = await execute_query(sql, limit=0)
        
        # Process the results
        data = []
        center_lat = 40.6431  # Default center (NJ-07)
        center_lon = -74.5464
        
        if query_result.get('rows'):
            # Get column indices
            columns = query_result.get('columns', [])
            lat_idx = columns.index('latitude') if 'latitude' in columns else None
            lon_idx = columns.index('longitude') if 'longitude' in columns else None
            
            # Process rows and calculate center
            total_lat = 0
            total_lon = 0
            valid_coords = 0
            
            for row in query_result['rows']:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                
                # Extract coordinates
                if lat_idx is not None and lon_idx is not None:
                    lat = row[lat_idx]
                    lon = row[lon_idx]
                    if lat and lon:
                        row_dict['latitude'] = float(lat)
                        row_dict['longitude'] = float(lon)
                        total_lat += float(lat)
                        total_lon += float(lon)
                        valid_coords += 1
                
                data.append(row_dict)
            
            # Calculate center point from data
            if valid_coords > 0:
                center_lat = total_lat / valid_coords
                center_lon = total_lon / valid_coords
        
        return VisualizationResponse(
            type=viz_type,
            data=data,  # Return all data points
            query=sql,
            description=description,
            total_count=len(data),
            center_lat=center_lat,
            center_lon=center_lon
        )
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate visualization: {str(e)}")