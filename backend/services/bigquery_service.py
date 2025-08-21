import asyncio
import time
from typing import Dict, List, Any
import sys
import os

# Add parent directory to import ADK agent components
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool

async def execute_query(query: str, limit: int = 10000) -> Dict[str, Any]:
    """
    Execute a BigQuery query and return results
    """
    try:
        start_time = time.time()
        
        # Use the BigQuery tool from ADK agent
        tool = BigQueryReadOnlyTool()
        
        # Add limit if not present
        if "LIMIT" not in query.upper():
            query = f"{query} LIMIT {limit}"
        
        # Execute query in thread pool
        result = await asyncio.to_thread(
            tool.run,
            {"query": query}
        )
        
        execution_time = time.time() - start_time
        
        # Parse result
        if isinstance(result, str):
            # If result is a string (error message), return empty result
            return {
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time": execution_time,
                "query": query,
                "error": result
            }
        
        # Extract columns and rows from result
        if isinstance(result, list) and len(result) > 0:
            # Get column names from first row
            columns = list(result[0].keys()) if isinstance(result[0], dict) else []
            
            # Convert to row format
            rows = []
            for row in result:
                if isinstance(row, dict):
                    rows.append([row.get(col) for col in columns])
                else:
                    rows.append(row)
            
            return {
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows),
                "execution_time": execution_time,
                "query": query
            }
        
        return {
            "columns": [],
            "rows": [],
            "total_rows": 0,
            "execution_time": execution_time,
            "query": query
        }
        
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")