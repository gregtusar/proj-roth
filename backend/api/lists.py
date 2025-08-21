from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json
import csv
import io

from api.auth import get_current_user
from services.bigquery_service import execute_query

router = APIRouter()

class VoterList(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    query: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    row_count: Optional[int] = None
    user_id: Optional[str] = None

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List]
    total_rows: int
    execution_time: float
    query: str

# In-memory storage for demo (replace with Firestore in production)
voter_lists = {}

@router.get("/", response_model=List[VoterList])
async def get_user_lists(current_user: dict = Depends(get_current_user)):
    """
    Get all lists for the current user
    """
    user_lists = [
        VoterList(**list_data) for list_data in voter_lists.values()
        if list_data["user_id"] == current_user["id"]
    ]
    return user_lists

@router.get("/{list_id}", response_model=VoterList)
async def get_list(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific list
    """
    if list_id not in voter_lists:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = voter_lists[list_id]
    
    # Check ownership
    if list_data["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return VoterList(**list_data)

@router.post("/", response_model=VoterList)
async def create_list(
    list_data: VoterList,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new voter list
    """
    # Validate query (must be SELECT)
    if not list_data.query.strip().upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Query must be a SELECT statement"
        )
    
    # Generate ID and timestamps
    list_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    new_list = {
        "id": list_id,
        "name": list_data.name,
        "description": list_data.description,
        "query": list_data.query,
        "created_at": now,
        "updated_at": now,
        "row_count": None,
        "user_id": current_user["id"]
    }
    
    voter_lists[list_id] = new_list
    
    return VoterList(**new_list)

@router.put("/{list_id}", response_model=VoterList)
async def update_list(
    list_id: str,
    updates: VoterList,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing list
    """
    if list_id not in voter_lists:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = voter_lists[list_id]
    
    # Check ownership
    if list_data["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    if updates.name:
        list_data["name"] = updates.name
    if updates.description is not None:
        list_data["description"] = updates.description
    if updates.query:
        # Validate query
        if not updates.query.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Query must be a SELECT statement"
            )
        list_data["query"] = updates.query
        list_data["row_count"] = None  # Reset row count
    
    list_data["updated_at"] = datetime.utcnow().isoformat()
    
    return VoterList(**list_data)

@router.delete("/{list_id}")
async def delete_list(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a list
    """
    if list_id not in voter_lists:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = voter_lists[list_id]
    
    # Check ownership
    if list_data["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del voter_lists[list_id]
    
    return {"message": "List deleted successfully"}

@router.post("/{list_id}/run", response_model=QueryResult)
async def run_list_query(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Run the query for a list
    """
    if list_id not in voter_lists:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = voter_lists[list_id]
    
    # Check ownership
    if list_data["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Execute query using BigQuery service
        result = await execute_query(list_data["query"])
        
        # Update row count
        list_data["row_count"] = result["total_rows"]
        list_data["updated_at"] = datetime.utcnow().isoformat()
        
        return QueryResult(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )

@router.get("/{list_id}/export")
async def export_list_csv(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Export list results to CSV
    """
    if list_id not in voter_lists:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_data = voter_lists[list_id]
    
    # Check ownership
    if list_data["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Execute query
        result = await execute_query(list_data["query"])
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(result["columns"])
        
        # Write data
        writer.writerows(result["rows"])
        
        # Return CSV file
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={list_data['name'].replace(' ', '_')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )