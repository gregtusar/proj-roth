"""BigQuery service class for CRM and other services."""
import asyncio
import time
from typing import Dict, List, Any
from google.cloud import bigquery


class BigQueryService:
    """Service class for BigQuery operations."""
    
    def __init__(self):
        self.client = bigquery.Client(project='proj-roth')
    
    async def execute_query(self, query: str, limit: int = 100000) -> Dict[str, Any]:
        """
        Execute a BigQuery query and return results.
        
        Args:
            query: SQL query to execute
            limit: Maximum rows to return (default 100,000, use 0 for no limit)
        """
        try:
            start_time = time.time()
            
            # Add project prefix if not present
            if 'proj-roth' not in query:
                query = query.replace('voter_data.', '`proj-roth`.voter_data.')
            
            # Only add limit if not present AND limit > 0
            if limit > 0 and "LIMIT" not in query.upper():
                query = f"{query} LIMIT {limit}"
            
            # Configure job with caching enabled
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            job_config.use_legacy_sql = False
            
            # Execute query with caching
            query_job = self.client.query(query, job_config=job_config)
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
                    row_dict = {}
                    for col in columns:
                        value = row[col]
                        # Convert special types
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        elif value is None:
                            value = None
                        else:
                            value = str(value)
                        row_dict[col] = value
                    rows.append(row_dict)
            else:
                columns = []
                rows = []
            
            return {
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows),
                "execution_time": execution_time,
                "query": query
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"BigQuery error: {str(e)}")
            raise Exception(f"BigQuery error: {str(e)}")