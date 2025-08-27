from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from datetime import datetime
import json
import csv
import io

from api.auth import get_current_user
from services.bigquery_service import execute_query
from services.firestore_list_service import get_firestore_list_service
from models.voter_list import VoterList, CreateListRequest, UpdateListRequest, ListResponse

router = APIRouter()

@router.get("/", response_model=List[ListResponse])
async def get_user_lists(current_user: dict = Depends(get_current_user)):
    """Get all lists for the current user"""
    print(f"[Lists API] get_user_lists called with user: {current_user}", flush=True)
    service = get_firestore_list_service()
    
    if not service.connected:
        # Return empty list if Firestore is not available
        return []
    
    lists = await service.get_user_lists(current_user["id"])
    
    # Debug logging
    import sys
    print(f"[Lists API] Retrieved {len(lists)} lists from Firestore for user {current_user['id']}", flush=True)
    sys.stdout.flush()
    for lst in lists:
        print(f"  - List: {lst.name}, updated_at type: {type(lst.updated_at)}, value: {lst.updated_at}", flush=True)
    
    # Convert to response format
    response_lists = []
    for lst in lists:
        try:
            response_lists.append(
                ListResponse(
                    id=lst.id,
                    name=lst.name,
                    description=lst.description,
                    query=lst.query,
                    prompt=getattr(lst, 'prompt', None),
                    row_count=lst.row_count,
                    created_at=lst.created_at.isoformat() if lst.created_at else datetime.utcnow().isoformat(),
                    updated_at=lst.updated_at.isoformat() if lst.updated_at else datetime.utcnow().isoformat()
                )
            )
        except Exception as e:
            print(f"[Lists API] Error converting list {lst.id}: {e}")
            # Skip this list if there's an error
            continue
    
    print(f"[Lists API] Final response contains {len(response_lists)} lists", flush=True)
    sys.stdout.flush()
    return response_lists

@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific list"""
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    lst = await service.get_list(list_id, current_user["id"])
    
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    
    return ListResponse(
        id=lst.id,
        name=lst.name,
        description=lst.description,
        query=lst.query,
        prompt=getattr(lst, 'prompt', None),
        row_count=lst.row_count,
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )

@router.post("/", response_model=ListResponse)
async def create_list(
    list_data: CreateListRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new voter list"""
    # Validate query (must be SELECT)
    if not list_data.query.strip().upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Query must be a SELECT statement"
        )
    
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Execute query to get row count
    try:
        result = await execute_query(list_data.query)
        row_count = len(result.get("rows", []))
    except Exception as e:
        row_count = 0
    
    # Create the list
    lst = await service.create_list(
        user_id=current_user["id"],
        user_email=current_user.get("email", ""),
        name=list_data.name,
        description=list_data.description,
        query=list_data.query,
        prompt=list_data.prompt,
        row_count=row_count
    )
    
    return ListResponse(
        id=lst.id,
        name=lst.name,
        description=lst.description,
        query=lst.query,
        prompt=getattr(lst, 'prompt', None),
        row_count=lst.row_count,
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )

@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: str,
    update_data: UpdateListRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a voter list"""
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # If query is being updated, validate and get new row count
    row_count = None
    if update_data.query:
        if not update_data.query.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Query must be a SELECT statement"
            )
        try:
            result = await execute_query(update_data.query)
            row_count = len(result.get("rows", []))
        except Exception:
            row_count = 0
    
    # Update the list
    success = await service.update_list(
        list_id=list_id,
        user_id=current_user["id"],
        name=update_data.name,
        description=update_data.description,
        query=update_data.query,
        prompt=update_data.prompt,
        row_count=row_count
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="List not found or access denied")
    
    # Get updated list
    lst = await service.get_list(list_id, current_user["id"])
    
    return ListResponse(
        id=lst.id,
        name=lst.name,
        description=lst.description,
        query=lst.query,
        prompt=getattr(lst, 'prompt', None),
        row_count=lst.row_count,
        created_at=lst.created_at.isoformat(),
        updated_at=lst.updated_at.isoformat()
    )

@router.delete("/{list_id}")
async def delete_list(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a voter list"""
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    success = await service.delete_list(list_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="List not found or access denied")
    
    return {"message": "List deleted successfully"}

@router.post("/{list_id}/run")
async def run_list_query(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Run a saved list's query and return results"""
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Get the list
    lst = await service.get_list(list_id, current_user["id"])
    
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Execute the query as-is
    query = lst.query
    
    try:
        result = await execute_query(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execute")
async def execute_list_query(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Execute a query and return results"""
    query = request.get("query", "")
    limit = request.get("limit", 1000)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if not query.strip().upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    # Execute query as-is without adding automatic limits
    
    try:
        result = await execute_query(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{list_id}/export")
async def export_list(
    list_id: str,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """Export list data in various formats"""
    service = get_firestore_list_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Get the list
    lst = await service.get_list(list_id, current_user["id"])
    
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Execute the query
    try:
        result = await execute_query(lst.query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if result.get("columns"):
            writer.writerow(result["columns"])
        
        # Write data
        for row in result.get("rows", []):
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={list_id}.csv"
            }
        )
    
    elif format == "json":
        # Return JSON format
        json_data = {
            "list_name": lst.name,
            "description": lst.description,
            "columns": result.get("columns", []),
            "data": result.get("rows", []),
            "total_rows": len(result.get("rows", [])),
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return Response(
            content=json.dumps(json_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={list_id}.json"
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")

@router.get("/search/{query}")
async def search_lists(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Search user's lists by name or description"""
    service = get_firestore_list_service()
    
    if not service.connected:
        return []
    
    lists = await service.search_lists(current_user["id"], query)
    
    return [
        ListResponse(
            id=lst.id,
            name=lst.name,
            description=lst.description,
            query=lst.query,
            row_count=lst.row_count,
            created_at=lst.created_at.isoformat(),
            updated_at=lst.updated_at.isoformat()
        )
        for lst in lists
    ]