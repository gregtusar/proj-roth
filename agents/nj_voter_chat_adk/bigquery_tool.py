from typing import Any, Dict
import time
import re
from google.cloud import bigquery
from google.api_core.client_options import ClientOptions
from .config import PROJECT_ID, BQ_LOCATION, ALLOWED_TABLES, MAX_ROWS, QUERY_TIMEOUT_SECONDS
from .policy import is_select_only, tables_within_allowlist

class BigQueryReadOnlyTool:
    name = "bigquery_select"
    description = "Executes read-only SELECT queries on approved tables with smart field mapping."

    FIELD_MAPPINGS = {
        'voter_id': 'id',
        'party': 'demo_party',
        'age': 'demo_age',
        'race': 'demo_race',
        'gender': 'demo_gender',
        'address': 'addr_residential_line1',
        'street': 'addr_residential_street_name',
        'street_name': 'addr_residential_street_name',
        'street_number': 'addr_residential_street_number',
        'city': 'addr_residential_city',
        'state': 'addr_residential_state',
        'zip': 'addr_residential_zip_code',
        'zip_code': 'addr_residential_zip_code',
        'county': 'county_name',
        'lat': 'latitude',
        'lng': 'longitude',
        'lon': 'longitude',
        'first_name': 'name_first',
        'last_name': 'name_last',
        'middle_name': 'name_middle',
    }

    def __init__(self, project_id: str = PROJECT_ID, location: str = BQ_LOCATION):
        self.project_id = project_id
        self.location = location
        self.client = None
        
    def _get_client(self):
        """Lazy initialization of BigQuery client to handle credential errors gracefully."""
        if self.client is None:
            try:
                self.client = bigquery.Client(project=self.project_id, client_options=ClientOptions(quota_project_id=self.project_id))
            except Exception as e:
                raise Exception(f"Failed to initialize BigQuery client: {str(e)}. Please check your Google Cloud credentials.")
        return self.client

    def _apply_field_mappings(self, sql: str) -> str:
        mapped_sql = sql
        
        for user_field, actual_field in self.FIELD_MAPPINGS.items():
            pattern = r'\b' + re.escape(user_field) + r'\b'
            mapped_sql = re.sub(pattern, actual_field, mapped_sql, flags=re.IGNORECASE)
        
        return mapped_sql

    def run(self, sql: str) -> Dict[str, Any]:
        try:
            if not is_select_only(sql):
                return {"error": "Only SELECT queries are allowed."}
            
            mapped_sql = self._apply_field_mappings(sql)
            
            ok, illegal = tables_within_allowlist(mapped_sql, ALLOWED_TABLES)
            if not ok:
                return {"error": f"Query references non-allowlisted tables: {', '.join(sorted(illegal))}"}
            
            job_config = bigquery.QueryJobConfig()
            job_config.use_legacy_sql = False
            job_config.labels = {"agent": "nj_voter_chat"}
            start = time.time()
            
            print(f"[DEBUG] Original SQL: {sql}")
            print(f"[DEBUG] Mapped SQL: {mapped_sql}")
            
            client = self._get_client()
            query_job = client.query(mapped_sql, job_config=job_config, location=self.location)
            result_iter = query_job.result(timeout=QUERY_TIMEOUT_SECONDS)
            elapsed = time.time() - start
            
            rows = []
            for i, r in enumerate(result_iter):
                if i >= MAX_ROWS:
                    break
                rows.append(dict(r))
            
            truncated = query_job.total_rows is not None and query_job.total_rows > len(rows)
            return {
                "rows": rows, 
                "row_count": len(rows), 
                "truncated": truncated, 
                "elapsed_sec": round(elapsed, 3), 
                "sql": mapped_sql,
                "original_sql": sql
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] BigQuery execution failed: {error_msg}")
            
            return {
                "error": f"BigQuery execution failed: {error_msg}",
                "sql": sql,
                "mapped_sql": getattr(self, '_last_mapped_sql', sql),
                "rows": [],
                "row_count": 0
            }
