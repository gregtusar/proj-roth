"""BigQuery service wrapper for CRM functionality."""
from backend.services import bigquery_service


class BigQueryService:
    """Wrapper class for BigQuery operations."""
    
    async def execute_query(self, query: str, limit: int = 100000):
        """Execute a BigQuery query."""
        return await bigquery_service.execute_query(query, limit)