from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from api.auth import get_current_user
from services.bigquery_service import execute_query
from google.cloud import bigquery

router = APIRouter()

class StreetData(BaseModel):
    street_name: str
    city: str
    county: str
    zip_code: Optional[int]
    republican_count: int
    democrat_count: int
    unaffiliated_count: int
    total_voters: int
    republican_pct: float
    democrat_pct: float
    unaffiliated_pct: float
    latitude: float
    longitude: float

class MapData(BaseModel):
    streets: List[StreetData]
    center_lat: float
    center_lon: float

@router.get("/street-party-data", response_model=MapData)
async def get_street_party_data(
    min_voters: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Get street-level party concentration data for mapping
    """
    query = f"""
    SELECT 
        street_name,
        city,
        county,
        zip_code,
        republican_count,
        democrat_count,
        unaffiliated_count,
        total_voters,
        republican_pct,
        democrat_pct,
        unaffiliated_pct,
        street_center_longitude as longitude,
        street_center_latitude as latitude
    FROM `proj-roth.voter_data.street_party_summary`
    WHERE total_voters >= {min_voters}
    -- Return all streets for proper visualization
    LIMIT 12000
    """
    
    try:
        # Use native BigQuery client to avoid field mapping issues
        client = bigquery.Client(project='proj-roth')
        query_job = client.query(query)
        results = query_job.result()
        
        streets = []
        for row in results:
            street_data = dict(row)
            streets.append(StreetData(**street_data))
        
        # Calculate center point
        if streets:
            center_lat = sum(s.latitude for s in streets) / len(streets)
            center_lon = sum(s.longitude for s in streets) / len(streets)
        else:
            center_lat = 40.65  # Default to NJ area
            center_lon = -74.60
        
        return MapData(
            streets=streets,
            center_lat=center_lat,
            center_lon=center_lon
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch street data: {str(e)}"
        )