import asyncio
import time
from typing import Dict, List, Any
from google.cloud import bigquery

async def execute_query(query: str, limit: int = 100000) -> Dict[str, Any]:
    """
    Execute a BigQuery query and return results
    
    Args:
        query: SQL query to execute
        limit: Maximum rows to return (default 100,000, use 0 for no limit)
    """
    try:
        start_time = time.time()
        
        # Use native BigQuery client for better control
        client = bigquery.Client(project='proj-roth')
        
        # Add project prefix if not present
        if 'proj-roth.' not in query:
            query = query.replace('voter_data.', '`proj-roth.voter_data.')
            query = query.replace('`proj-roth.voter_data.', '`proj-roth`.voter_data.')
        
        # Only add limit if not present AND limit > 0
        if limit > 0 and "LIMIT" not in query.upper():
            query = f"{query} LIMIT {limit}"
        
        # Execute query
        query_job = client.query(query)
        results = list(query_job.result())
        
        execution_time = time.time() - start_time
        
        # Extract columns and rows from result
        if results:
            # Get column names from first row
            first_row = results[0]
            columns = list(first_row.keys())
            
            # Convert to row format
            rows = []
            for row in results:
                row_data = []
                for col in columns:
                    value = row[col]
                    # Convert special types to JSON-serializable format
                    if hasattr(value, 'isoformat'):  # datetime
                        value = value.isoformat()
                    elif hasattr(value, 'to_eng_string'):  # Decimal
                        value = float(value)
                    elif value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
                        value = str(value)
                    row_data.append(value)
                rows.append(row_data)
            
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