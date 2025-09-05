"""Campaign management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from backend.campaigns import CampaignManager
from core.auth import get_current_user
from core.database import get_firestore_client, get_bigquery_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class CampaignCreate(BaseModel):
    name: str
    list_id: str
    subject_line: str
    google_doc_url: str

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject_line: Optional[str] = None
    google_doc_url: Optional[str] = None

class TestEmail(BaseModel):
    test_email: str

# Initialize campaign manager
campaign_manager = None

def get_campaign_manager():
    global campaign_manager
    if campaign_manager is None:
        campaign_manager = CampaignManager(
            get_firestore_client(),
            get_bigquery_client()
        )
    return campaign_manager

@router.post("/campaigns")
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new email campaign."""
    try:
        manager = get_campaign_manager()
        
        # Add user info to campaign data
        data = campaign_data.dict()
        data['created_by'] = current_user.get('email', 'unknown')
        
        campaign_id = manager.create_campaign(data)
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Campaign created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """List all campaigns with optional filtering."""
    try:
        manager = get_campaign_manager()
        campaigns = manager.list_campaigns(status=status, limit=limit, offset=offset)
        
        return {
            "success": True,
            "campaigns": campaigns,
            "count": len(campaigns)
        }
    except Exception as e:
        logger.error(f"Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get campaign details."""
    try:
        manager = get_campaign_manager()
        campaign = manager.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return {
            "success": True,
            "campaign": campaign
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update campaign details."""
    try:
        manager = get_campaign_manager()
        
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = manager.update_campaign(campaign_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update campaign")
        
        return {
            "success": True,
            "message": "Campaign updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a campaign."""
    try:
        manager = get_campaign_manager()
        
        # Check if campaign exists
        campaign = manager.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Don't delete campaigns that have been sent
        if campaign['status'] in ['sending', 'sent']:
            raise HTTPException(status_code=400, detail="Cannot delete sent campaigns")
        
        # Delete the campaign
        db = get_firestore_client()
        db.collection('campaigns').document(campaign_id).delete()
        
        return {
            "success": True,
            "message": "Campaign deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Send a campaign to all recipients."""
    try:
        manager = get_campaign_manager()
        
        # Check campaign status
        campaign = manager.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign['status'] in ['sending', 'sent']:
            raise HTTPException(status_code=400, detail="Campaign already sent")
        
        # Send campaign in background
        background_tasks.add_task(manager.send_campaign, campaign_id)
        
        return {
            "success": True,
            "message": "Campaign sending started",
            "campaign_id": campaign_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/test")
async def send_test_email(
    campaign_id: str,
    test_data: TestEmail,
    current_user: Dict = Depends(get_current_user)
):
    """Send a test email for a campaign."""
    try:
        manager = get_campaign_manager()
        
        # Check campaign exists
        campaign = manager.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Send test email
        result = manager.send_campaign(campaign_id, test_email=test_data.test_email)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to send test email'))
        
        return {
            "success": True,
            "message": f"Test email sent to {test_data.test_email}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed statistics for a campaign."""
    try:
        manager = get_campaign_manager()
        stats = manager.get_campaign_stats(campaign_id)
        
        if stats is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return {
            "success": True,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/events")
async def get_campaign_events(
    campaign_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    current_user: Dict = Depends(get_current_user)
):
    """Get event stream for a campaign."""
    try:
        db = get_firestore_client()
        
        # Build query
        query = db.collection('events').where('email_data.campaign_id', '==', campaign_id)
        
        if event_type:
            query = query.where('event_type', '==', event_type)
        
        query = query.order_by('timestamp', direction='DESCENDING').limit(limit)
        
        # Execute query
        events = []
        for doc in query.stream():
            event = doc.to_dict()
            events.append(event)
        
        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Failed to get campaign events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(request: Request):
    """Handle SendGrid webhook events."""
    try:
        # Parse webhook data
        events = await request.json()
        
        # Log for debugging
        logger.info(f"Received {len(events)} SendGrid events")
        
        # Process events
        manager = get_campaign_manager()
        manager.handle_sendgrid_webhook(events)
        
        return {"success": True, "received": len(events)}
    except Exception as e:
        logger.error(f"Failed to process SendGrid webhook: {e}")
        # SendGrid expects 200 response even on error
        return {"success": False, "error": str(e)}