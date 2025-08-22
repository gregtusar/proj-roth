from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json
import csv
import io
import asyncio

from api.auth import get_current_user
from services.bigquery_service import execute_query
from agents.nj_voter_chat_adk.agent import NJVoterChatAgent

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
    user_email: Optional[str] = None

class VoterListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    query: Optional[str] = None

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List]
    total_rows: int
    execution_time: float
    query: str

# In-memory storage for demo (replace with Firestore in production)
voter_lists = {}

# Add some sample lists for demo
def init_sample_lists():
    sample_lists = [
        {
            "id": "sample-1",
            "name": "High-Propensity Democratic Voters",
            "description": "Democrats who voted in 3+ of the last 4 elections",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party 
                       FROM `proj-roth.voter_data.voters` 
                       WHERE demo_party = 'DEMOCRAT' 
                       AND addr_residential_city IN ('SUMMIT', 'WESTFIELD', 'BERKELEY HEIGHTS')
                       LIMIT 100""",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"  # Your Google ID
        },
        {
            "id": "sample-2", 
            "name": "Unaffiliated Voters in Union County",
            "description": "Independent voters who may be persuadable",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party
                       FROM `proj-roth.voter_data.voters`
                       WHERE demo_party = 'UNA'
                       AND county_name = 'UNION'
                       LIMIT 100""",
            "created_at": "2024-01-10T10:00:00",
            "updated_at": "2024-01-10T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-3",
            "name": "Young Voters (18-35)",
            "description": "Millennial and Gen Z voters",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party, demo_age
                       FROM `proj-roth.voter_data.voters`
                       WHERE demo_age BETWEEN 18 AND 35
                       LIMIT 100""",
            "created_at": "2024-01-05T10:00:00",
            "updated_at": "2024-01-05T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-4",
            "name": "Top 50 Democratic Donors in Bernardsville",
            "description": "High-value donors to Democratic campaigns",
            "query": """SELECT DISTINCT 
                         v.name_first, 
                         v.name_last, 
                         v.addr_residential_line1,
                         v.addr_residential_city,
                         COUNT(d.donation_id) as donation_count,
                         SUM(d.amount) as total_donated
                       FROM `proj-roth.voter_data.voters` v
                       JOIN `proj-roth.voter_data.donations` d ON v.id = d.voter_id
                       WHERE v.addr_residential_city = 'BERNARDSVILLE'
                       AND d.party = 'DEMOCRAT'
                       GROUP BY v.name_first, v.name_last, v.addr_residential_line1, v.addr_residential_city
                       ORDER BY total_donated DESC
                       LIMIT 50""",
            "created_at": "2024-01-20T10:00:00",
            "updated_at": "2024-01-20T10:00:00", 
            "row_count": 50,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-5",
            "name": "Senior Voters (65+)",
            "description": "Active senior voters in the district",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party, demo_age
                       FROM `proj-roth.voter_data.voters`
                       WHERE demo_age >= 65
                       AND demo_status = 'ACTIVE'
                       LIMIT 100""",
            "created_at": "2024-01-18T10:00:00",
            "updated_at": "2024-01-18T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-6",
            "name": "New Registrations (Last 90 Days)",
            "description": "Recently registered voters",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party, demo_registration_date
                       FROM `proj-roth.voter_data.voters`
                       WHERE DATE(demo_registration_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                       ORDER BY demo_registration_date DESC
                       LIMIT 100""",
            "created_at": "2024-01-22T10:00:00",
            "updated_at": "2024-01-22T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-7",
            "name": "Split-Ticket Voters",
            "description": "Voters with mixed party voting history",
            "query": """SELECT v.name_first, v.name_last, v.addr_residential_city, v.demo_party,
                              COUNT(DISTINCT h.party_voted) as parties_voted_for
                       FROM `proj-roth.voter_data.voters` v
                       JOIN `proj-roth.voter_data.voting_history` h ON v.id = h.voter_id
                       GROUP BY v.name_first, v.name_last, v.addr_residential_city, v.demo_party
                       HAVING parties_voted_for > 1
                       LIMIT 100""",
            "created_at": "2024-01-12T10:00:00",
            "updated_at": "2024-01-12T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        },
        {
            "id": "sample-8",
            "name": "High-Frequency Voters",
            "description": "Voters who voted in 80%+ of recent elections",
            "query": """SELECT name_first, name_last, addr_residential_city, demo_party,
                              vote_history_general_2022, vote_history_general_2020
                       FROM `proj-roth.voter_data.voters`
                       WHERE vote_history_general_2022 = 'Y'
                       AND vote_history_general_2020 = 'Y' 
                       AND vote_history_general_2018 = 'Y'
                       LIMIT 100""",
            "created_at": "2024-01-08T10:00:00",
            "updated_at": "2024-01-08T10:00:00",
            "row_count": 100,
            "user_id": "116551015281252125032"
        }
    ]
    
    for list_data in sample_lists:
        voter_lists[list_data["id"]] = list_data

# Initialize sample lists on startup
init_sample_lists()

@router.get("/", response_model=List[VoterList])
async def get_user_lists(current_user: dict = Depends(get_current_user)):
    """
    Get all lists for the current user from BigQuery
    """
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    # First try to get lists from BigQuery
    try:
        query = f"""
        SELECT 
            list_id,
            list_name,
            description_text,
            sql_query,
            created_at,
            updated_at,
            row_count,
            user_id,
            user_email
        FROM `proj-roth.voter_data.voter_lists`
        WHERE is_active = TRUE
        ORDER BY updated_at DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        # Filter out locally deleted items (streaming buffer workaround)
        deleted_ids = getattr(delete_list, 'deleted_ids', set()) if 'delete_list' in globals() else set()
        
        user_lists = []
        for row in results:
            # Skip if this ID was recently deleted
            if row.list_id in deleted_ids:
                continue
                
            list_data = {
                "id": row.list_id,
                "name": row.list_name,
                "description": row.description_text or "",
                "query": row.sql_query,
                "created_at": row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat(),
                "updated_at": row.updated_at.isoformat() if row.updated_at else datetime.utcnow().isoformat(),
                "row_count": row.row_count,
                "user_id": row.user_id or current_user["id"],
                "user_email": row.user_email or current_user.get("email", "")
            }
            user_lists.append(VoterList(**list_data))
        
        return user_lists
        
    except Exception as e:
        # Fall back to in-memory lists if BigQuery fails
        print(f"Error fetching from BigQuery: {e}")
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
    Create a new voter list in BigQuery
    """
    # Validate query (must be SELECT)
    if not list_data.query.strip().upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Query must be a SELECT statement"
        )
    
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    # Generate ID and timestamps
    list_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    try:
        # Insert into BigQuery
        insert_query = f"""
        INSERT INTO `proj-roth.voter_data.voter_lists` (
            list_id,
            user_id,
            user_email,
            list_name,
            description_text,
            sql_query,
            row_count,
            is_shared,
            is_active,
            created_at,
            updated_at,
            created_by_model,
            query_execution_time_ms,
            last_accessed_at,
            access_count,
            shared_with_emails,
            share_type
        ) VALUES (
            '{list_id}',
            '{current_user["id"]}',
            '{current_user.get("email", "")}',
            '{list_data.name.replace("'", "''")}',
            '{list_data.description.replace("'", "''") if list_data.description else ""}',
            '{list_data.query.replace("'", "''")}',
            NULL,
            FALSE,
            TRUE,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            'user_created',
            NULL,
            CURRENT_TIMESTAMP(),
            0,
            NULL,
            NULL
        )
        """
        
        query_job = client.query(insert_query)
        query_job.result()  # Wait for completion
        
        # Return the created list
        return VoterList(
            id=list_id,
            name=list_data.name,
            description=list_data.description or "",
            query=list_data.query,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            row_count=None,
            user_id=current_user["id"],
            user_email=current_user.get("email", "")
        )
        
    except Exception as e:
        # Fall back to in-memory storage if BigQuery fails
        print(f"Failed to insert into BigQuery: {e}")
        
        new_list = {
            "id": list_id,
            "name": list_data.name,
            "description": list_data.description,
            "query": list_data.query,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "row_count": None,
            "user_id": current_user["id"],
            "user_email": current_user.get("email", "")
        }
        
        voter_lists[list_id] = new_list
        
        return VoterList(**new_list)

@router.put("/{list_id}", response_model=VoterList)
async def update_list(
    list_id: str,
    updates: VoterListUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing list in BigQuery
    """
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    try:
        # Check if list exists in BigQuery
        check_query = f"""
        SELECT *
        FROM `proj-roth.voter_data.voter_lists`
        WHERE list_id = '{list_id}'
        """
        
        query_job = client.query(check_query)
        results = list(query_job.result())
        
        if results:
            # Update in BigQuery
            update_parts = []
            
            if updates.name:
                safe_name = updates.name.replace("'", "''")
                update_parts.append(f"list_name = '{safe_name}'")
            if updates.description is not None:
                safe_desc = updates.description.replace("'", "''")
                update_parts.append(f"description_text = '{safe_desc}'")
            if updates.query:
                # Validate query
                if not updates.query.strip().upper().startswith("SELECT"):
                    raise HTTPException(
                        status_code=400,
                        detail="Query must be a SELECT statement"
                    )
                safe_query = updates.query.replace("'", "''")
                update_parts.append(f"sql_query = '{safe_query}'")
                update_parts.append("row_count = NULL")  # Reset row count
            
            if update_parts:
                update_parts.append("updated_at = CURRENT_TIMESTAMP()")
                
                update_query = f"""
                UPDATE `proj-roth.voter_data.voter_lists`
                SET {', '.join(update_parts)}
                WHERE list_id = '{list_id}'
                """
                
                query_job = client.query(update_query)
                query_job.result()  # Wait for completion
            
            # Fetch updated record
            fetch_query = f"""
            SELECT *
            FROM `proj-roth.voter_data.voter_lists`
            WHERE list_id = '{list_id}'
            """
            
            query_job = client.query(fetch_query)
            updated_row = list(query_job.result())[0]
            
            return VoterList(
                id=updated_row.list_id,
                name=updated_row.list_name,
                description=updated_row.description_text or "",
                query=updated_row.sql_query,
                created_at=updated_row.created_at.isoformat() if updated_row.created_at else datetime.utcnow().isoformat(),
                updated_at=updated_row.updated_at.isoformat() if updated_row.updated_at else datetime.utcnow().isoformat(),
                row_count=updated_row.row_count,
                user_id=updated_row.user_id or current_user["id"],
                user_email=updated_row.user_email or current_user.get("email", "")
            )
            
        elif list_id in voter_lists:
            # Fall back to in-memory update
            list_data = voter_lists[list_id]
            
            if updates.name:
                list_data["name"] = updates.name
            if updates.description is not None:
                list_data["description"] = updates.description
            if updates.query:
                if not updates.query.strip().upper().startswith("SELECT"):
                    raise HTTPException(
                        status_code=400,
                        detail="Query must be a SELECT statement"
                    )
                list_data["query"] = updates.query
                list_data["row_count"] = None
            
            list_data["updated_at"] = datetime.utcnow().isoformat()
            
            return VoterList(**list_data)
        else:
            raise HTTPException(status_code=404, detail="List not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update list: {str(e)}"
        )

@router.delete("/{list_id}")
async def delete_list(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a list (mark as inactive in BigQuery)
    """
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    try:
        # First check if the list exists
        check_query = f"""
        SELECT list_id, user_id
        FROM `proj-roth.voter_data.voter_lists`
        WHERE list_id = '{list_id}'
        """
        
        print(f"Checking for list: {list_id}")
        query_job = client.query(check_query)
        results = list(query_job.result())
        
        if not results:
            # Check in-memory storage as fallback
            if list_id in voter_lists:
                del voter_lists[list_id]
                return {"message": "List deleted successfully"}
            print(f"List not found: {list_id}")
            raise HTTPException(status_code=404, detail="List not found")
        
        print(f"Found list, attempting to delete: {list_id}")
        
        # Try to mark as inactive - this may fail due to streaming buffer
        try:
            update_query = f"""
            UPDATE `proj-roth.voter_data.voter_lists`
            SET is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP()
            WHERE list_id = '{list_id}'
            """
            
            print(f"Running update query: {update_query}")
            query_job = client.query(update_query)
            query_job.result()  # Wait for the query to complete
            print(f"Update completed for list: {list_id}")
        except Exception as bq_error:
            # If BigQuery update fails due to streaming buffer, track deletion locally
            print(f"BigQuery update failed (likely streaming buffer): {str(bq_error)}")
            # For now, we'll just remove from in-memory and return success
            # In production, you'd want to track this in a separate deletion table
            pass
        
        # Also remove from in-memory if it exists there
        if list_id in voter_lists:
            del voter_lists[list_id]
        
        # Add to a local deletion set to filter out in GET requests
        if not hasattr(delete_list, 'deleted_ids'):
            delete_list.deleted_ids = set()
        delete_list.deleted_ids.add(list_id)
        
        return {"message": "List deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting list {list_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete list: {str(e)}"
        )

@router.post("/{list_id}/regenerate-sql")
async def regenerate_sql_query(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Use AI to regenerate SQL query from the list description
    """
    # First try to get from BigQuery
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    try:
        query = f"""
        SELECT 
            list_id,
            description_text,
            user_id
        FROM `proj-roth.voter_data.voter_lists`
        WHERE list_id = '{list_id}'
        """
        
        query_job = client.query(query)
        results = list(query_job.result())
        
        if results:
            list_data = {
                "description": results[0].description_text,
                "user_id": results[0].user_id
            }
        elif list_id in voter_lists:
            # Fall back to in-memory storage
            list_data = voter_lists[list_id]
        else:
            raise HTTPException(status_code=404, detail="List not found")
        
        if not list_data.get("description"):
            raise HTTPException(status_code=400, detail="List has no description to generate query from")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get list: {str(e)}")
    
    try:
        # Use the agent to generate SQL from description
        agent = NJVoterChatAgent()
        
        # Create a more conversational prompt for the agent
        prompt = f"""Create a SQL query to find: {list_data['description']}
        
        Use the voters table and include relevant columns. Do NOT add a LIMIT clause - we want all matching records."""
        
        # Use asyncio to run the synchronous chat method
        result = await asyncio.to_thread(agent.chat, prompt)
        
        print(f"Agent result type: {type(result)}")
        print(f"Agent result: {result}")
        
        # Extract just the SQL from the response
        if isinstance(result, dict):
            sql_query = result.get("output", "").strip()
        else:
            sql_query = str(result).strip()
        
        print(f"Extracted SQL: {sql_query}")
        
        # Remove any markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Extract just the SELECT statement if there's additional text
        lines = sql_query.split('\n')
        sql_lines = []
        in_sql = False
        for line in lines:
            if line.strip().upper().startswith('SELECT'):
                in_sql = True
            if in_sql:
                sql_lines.append(line)
                if ';' in line:
                    break
        
        if sql_lines:
            sql_query = '\n'.join(sql_lines).replace(';', '').strip()
        
        # Ensure it starts with SELECT
        if not sql_query.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Generated query must be a SELECT statement"
            )
        
        # Update the list with the new query in BigQuery if it exists there
        from google.cloud import bigquery
        client = bigquery.Client(project='proj-roth')
        
        try:
            update_query = f"""
            UPDATE `proj-roth.voter_data.voter_lists`
            SET sql_query = '{sql_query.replace("'", "''")}',
                updated_at = CURRENT_TIMESTAMP()
            WHERE list_id = '{list_id}'
            """
            
            query_job = client.query(update_query)
            query_job.result()  # Wait for completion
        except:
            # If BigQuery update fails, update in-memory
            if list_id in voter_lists:
                list_data["query"] = sql_query
                list_data["updated_at"] = datetime.utcnow().isoformat()
        
        return {"query": sql_query}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL: {str(e)}"
        )

@router.post("/{list_id}/run", response_model=QueryResult)
async def run_list_query(
    list_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Run the query for a list
    """
    # First try to get from BigQuery
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    try:
        query = f"""
        SELECT 
            list_id,
            sql_query,
            user_id
        FROM `proj-roth.voter_data.voter_lists`
        WHERE list_id = '{list_id}'
        """
        
        query_job = client.query(query)
        results = list(query_job.result())
        
        if results:
            list_data = {
                "query": results[0].sql_query,
                "user_id": results[0].user_id
            }
        elif list_id in voter_lists:
            # Fall back to in-memory storage
            list_data = voter_lists[list_id]
        else:
            raise HTTPException(status_code=404, detail="List not found")
        
        # Execute query using BigQuery service
        # Use limit=0 to avoid adding any automatic LIMIT clause
        result = await execute_query(list_data["query"], limit=0)
        
        # Update row count in BigQuery
        if result["total_rows"] > 0:
            try:
                update_query = f"""
                UPDATE `proj-roth.voter_data.voter_lists`
                SET row_count = {result["total_rows"]},
                    last_accessed_at = CURRENT_TIMESTAMP(),
                    access_count = access_count + 1
                WHERE list_id = '{list_id}'
                """
                
                query_job = client.query(update_query)
                query_job.result()  # Wait for completion
            except:
                # If BigQuery update fails, update in-memory
                if list_id in voter_lists:
                    voter_lists[list_id]["row_count"] = result["total_rows"]
        
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