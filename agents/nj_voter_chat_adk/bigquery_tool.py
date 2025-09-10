from typing import Any, Dict
import time
import re
import json
import datetime
from decimal import Decimal
from google.cloud import bigquery
from google.api_core.client_options import ClientOptions
from .config import PROJECT_ID, BQ_LOCATION, ALLOWED_TABLES, MAX_ROWS, QUERY_TIMEOUT_SECONDS
from .policy import is_select_only, tables_within_allowlist
from .debug_config import debug_print, error_print

def convert_decimal(obj):
    """Convert Decimal and date objects to JSON-serializable types."""
    
    if isinstance(obj, Decimal):
        # Convert to float for numeric values
        return float(obj)
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        # Convert date/datetime to ISO format string
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj

class BigQueryReadOnlyTool:
    name = "bigquery_select"
    description = """Executes read-only SELECT queries on approved tables with smart field mapping and geospatial support. 
    
    NEW: Normalized schema with relationship queries available:
    - Use voter_geo_view for complete voter info with addresses and geocoding
    - Use donor_view to find campaign contributors and match them to voters
    - Join tables on master_id to link individuals across datasets
    - PDL enrichment: pdl_enrichment table has job_title, job_company as columns; detailed data in pdl_data JSON field
    
    PDL TABLE NOTE: The pdl_enrichment table stores ALL data in pdl_data JSON (clean schema, no redundant columns).
    Core columns: master_id, pdl_id, likelihood, pdl_data (JSON), has_email, has_linkedin, enriched_at.
    Extract fields using: JSON_EXTRACT_SCALAR(pdl_data, '$.job_title'), JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_name'), etc.
    OR use pdl_enrichment_view for convenience - it has virtual columns extracted from JSON.
    
    Supports BigQuery Geography functions like ST_DISTANCE, ST_GEOGPOINT for location-based queries. 
    IMPORTANT: demo_party field values must be exactly 'REPUBLICAN', 'DEMOCRAT', or 'UNAFFILIATED' (case-sensitive)."""

    FIELD_MAPPINGS = {
        # Original schema mappings
        'voter_id': 'id',
        'party': 'demo_party',
        'age': 'demo_age',
        'race': 'demo_race',
        'gender': 'demo_gender',
        'address': 'addr_residential_line1',
        'street': 'addr_residential_street_name',
        'street_name': 'addr_residential_street_name',
        'street_number': 'addr_residential_street_number',
        # Removed 'city' mapping - it conflicts with normalized schema
        # 'city': 'addr_residential_city',  # REMOVED - use city as-is in new schema
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
        # New normalized schema mappings
        'person_id': 'master_id',
        'individual_id': 'master_id',
        'location_id': 'address_id',
        'standardized_address': 'standardized_address',
        'standardized_name': 'standardized_name',
        'vendor_id': 'vendor_voter_id',
        'amount': 'contribution_amount',
        'donor': 'master_id',
        'donation': 'contribution_amount',
        # Geospatial function mappings
        'distance': 'ST_DISTANCE',
        'point': 'ST_GEOGPOINT',
        'within': 'ST_DWITHIN',
        'buffer': 'ST_BUFFER',
        'contains': 'ST_CONTAINS',
        'area': 'ST_AREA',
        'length': 'ST_LENGTH',
        # Party value mappings
        "'Democratic'": "'DEMOCRAT'",
        "'Democrats'": "'DEMOCRAT'",
        "'democrat'": "'DEMOCRAT'",
        "'democratic'": "'DEMOCRAT'",
        "'Republican'": "'REPUBLICAN'",
        "'Republicans'": "'REPUBLICAN'",
        "'republican'": "'REPUBLICAN'",
        "'Unaffiliated'": "'UNAFFILIATED'",
        "'unaffiliated'": "'UNAFFILIATED'",
        "'Independent'": "'UNAFFILIATED'",
        "'independent'": "'UNAFFILIATED'",
        # Congressional district mappings
        "'NJ-07'": "'NJ CONGRESSIONAL DISTRICT 07'",
        "'NJ-7'": "'NJ CONGRESSIONAL DISTRICT 07'",
        "'NJ07'": "'NJ CONGRESSIONAL DISTRICT 07'",
        "'District 7'": "'NJ CONGRESSIONAL DISTRICT 07'",
        "'7th District'": "'NJ CONGRESSIONAL DISTRICT 07'",
        "'7th Congressional District'": "'NJ CONGRESSIONAL DISTRICT 07'",
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
        
        # Check if query references PDL enrichment tables
        pdl_pattern = r'\bpdl_enrichment\b|\bpdl_enrichment_view\b'
        references_pdl = bool(re.search(pdl_pattern, sql, re.IGNORECASE))
        
        # Fields that should NOT be mapped for PDL tables
        pdl_excluded_mappings = {
            'first_name',  # PDL view uses first_name, not name_first
            'last_name',   # PDL view uses last_name, not name_last
            'middle_name', # PDL doesn't have middle_name
            'city',        # PDL might have location_city in JSON
        }
        
        field_mappings = {k: v for k, v in self.FIELD_MAPPINGS.items() if not k.startswith("'")}
        
        # If PDL table is referenced, skip mappings that would break PDL queries
        if references_pdl:
            field_mappings = {k: v for k, v in field_mappings.items() if k not in pdl_excluded_mappings}
        
        for user_field, actual_field in field_mappings.items():
            pattern = r'\b' + re.escape(user_field) + r'\b'
            mapped_sql = re.sub(pattern, actual_field, mapped_sql, flags=re.IGNORECASE)
        
        value_mappings = {k: v for k, v in self.FIELD_MAPPINGS.items() if k.startswith("'")}
        for user_value, actual_value in value_mappings.items():
            user_value_unquoted = user_value.strip("'")
            pattern = r"'" + re.escape(user_value_unquoted) + r"'"
            mapped_sql = re.sub(pattern, actual_value, mapped_sql, flags=re.IGNORECASE)
        
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
            job_config.use_query_cache = True  # Enable query caching for performance
            job_config.labels = {"agent": "nj_voter_chat"}
            start = time.time()
            
            debug_print(f"[DEBUG] Original SQL: {sql}")
            debug_print(f"[DEBUG] Mapped SQL: {mapped_sql}")
            
            client = self._get_client()
            query_job = client.query(mapped_sql, job_config=job_config, location=self.location)
            result_iter = query_job.result(timeout=QUERY_TIMEOUT_SECONDS)
            elapsed = time.time() - start
            
            rows = []
            for i, r in enumerate(result_iter):
                if i >= MAX_ROWS:
                    break
                # Convert row to dict and handle Decimal types
                row_dict = dict(r)
                row_dict = convert_decimal(row_dict)
                rows.append(row_dict)
            
            total_rows = getattr(query_job, 'total_rows', None)
            truncated = total_rows is not None and total_rows > len(rows)
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
            error_print(f"[ERROR] BigQuery execution failed: {error_msg}")
            
            return {
                "error": f"BigQuery execution failed: {error_msg}",
                "sql": sql,
                "mapped_sql": getattr(self, '_last_mapped_sql', sql),
                "rows": [],
                "row_count": 0
            }
