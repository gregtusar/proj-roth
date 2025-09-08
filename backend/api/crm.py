"""CRM API endpoints for voter management."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from core.config import get_settings
from services.crm_service import CRMService
from services.voter_index_service import VoterIndexService
from api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crm", tags=["crm"])

settings = get_settings()
crm_service = CRMService()
voter_index_service = VoterIndexService()


class VoterSearchResult(BaseModel):
    """Voter search result for typeahead."""
    master_id: str
    name: str
    address: str
    age: Optional[int]
    party: Optional[str]


class CRMEvent(BaseModel):
    """CRM event model."""
    event_type: str = Field(..., description="Type of event (e.g., 'call_notes', 'meeting', 'email')")
    notes: str = Field(..., description="Event notes or description")
    voter_master_id: str = Field(..., description="Master ID of the voter")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional event metadata")


class CRMEventResponse(BaseModel):
    """CRM event response model."""
    event_id: str
    event_type: str
    notes: str
    voter_master_id: str
    created_by: str
    created_at: datetime
    metadata: Dict[str, Any]


@router.get("/search", response_model=List[VoterSearchResult])
async def search_voters(
    q: str = Query(..., min_length=2, description="Search query (last, first format)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    current_user: dict = Depends(get_current_user)
) -> List[VoterSearchResult]:
    """
    Search for voters with typeahead functionality.
    Expects format: "last, first" or partial names.
    """
    try:
        logger.info(f"[CRM] Searching voters with query: {q}, limit: {limit}")
        results = await crm_service.search_voters(q, limit, current_user.get('sub'))
        return results
    except Exception as e:
        logger.error(f"[CRM] Error searching voters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching voters: {str(e)}")


@router.get("/voter/{master_id}")
async def get_voter_profile(
    master_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive voter profile including all available information.
    """
    try:
        logger.info(f"[CRM] Fetching voter profile for master_id: {master_id}")
        profile = await crm_service.get_voter_profile(master_id, current_user.get('sub'))
        if not profile:
            raise HTTPException(status_code=404, detail="Voter not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM] Error fetching voter profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching voter profile: {str(e)}")


@router.post("/enrich/{master_id}")
async def enrich_voter(
    master_id: str,
    force: bool = Query(False, description="Force re-enrichment even if data exists"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger PDL enrichment for a voter.
    """
    try:
        logger.info(f"[CRM] Enriching voter {master_id}, force={force}")
        enrichment_data = await crm_service.enrich_voter(master_id, force, current_user.get('sub'))
        return enrichment_data
    except Exception as e:
        logger.error(f"[CRM] Error enriching voter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enriching voter: {str(e)}")


@router.get("/events/{master_id}", response_model=List[CRMEventResponse])
async def get_voter_events(
    master_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum events to return"),
    current_user: dict = Depends(get_current_user)
) -> List[CRMEventResponse]:
    """
    Get all CRM events for a voter.
    """
    try:
        logger.info(f"[CRM] Fetching events for voter {master_id}")
        events = await crm_service.get_voter_events(
            master_id, 
            event_type=event_type, 
            limit=limit,
            user_id=current_user.get('sub')
        )
        return events
    except Exception as e:
        logger.error(f"[CRM] Error fetching events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")


@router.post("/events", response_model=CRMEventResponse)
async def create_event(
    event: CRMEvent,
    current_user: dict = Depends(get_current_user)
) -> CRMEventResponse:
    """
    Create a new CRM event for a voter.
    """
    try:
        logger.info(f"[CRM] Creating event for voter {event.voter_master_id}")
        created_event = await crm_service.create_event(
            voter_master_id=event.voter_master_id,
            event_type=event.event_type,
            notes=event.notes,
            metadata=event.metadata or {},
            user_id=current_user.get('sub')
        )
        return created_event
    except Exception as e:
        logger.error(f"[CRM] Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")


@router.get("/voting-history/{master_id}")
async def get_voting_history(
    master_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get voting history for a voter (primaries and generals).
    """
    try:
        logger.info(f"[CRM] Fetching voting history for {master_id}")
        history = await crm_service.get_voting_history(master_id, current_user.get('sub'))
        return history
    except Exception as e:
        logger.error(f"[CRM] Error fetching voting history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching voting history: {str(e)}")


@router.get("/donation-history/{master_id}")
async def get_donation_history(
    master_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get donation history for a voter.
    """
    try:
        logger.info(f"[CRM] Fetching donation history for {master_id}")
        history = await crm_service.get_donation_history(master_id, current_user.get('sub'))
        return history
    except Exception as e:
        logger.error(f"[CRM] Error fetching donation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching donation history: {str(e)}")


@router.post("/index/rebuild")
async def rebuild_voter_index(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rebuild the voter name index from BigQuery.
    This will refresh the cached trie structure for fast typeahead search.
    """
    try:
        logger.info(f"[CRM] Rebuilding voter index requested by {current_user.get('email')}")
        result = await voter_index_service.rebuild_index()
        return result
    except Exception as e:
        logger.error(f"[CRM] Error rebuilding index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rebuilding index: {str(e)}")


@router.get("/index/stats")
async def get_index_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get statistics about the voter name index.
    """
    try:
        stats = await voter_index_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"[CRM] Error getting index stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting index stats: {str(e)}")