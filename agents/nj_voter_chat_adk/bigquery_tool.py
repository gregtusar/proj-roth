from typing import Any, Dict
import time
from google.cloud import bigquery
from google.api_core.client_options import ClientOptions
from config import PROJECT_ID, BQ_LOCATION, ALLOWED_TABLES, MAX_ROWS, QUERY_TIMEOUT_SECONDS
from policy import is_select_only, tables_within_allowlist

class BigQueryReadOnlyTool:
    name = "bigquery_select"
    description = "Executes read-only SELECT queries on approved tables."

    def __init__(self, project_id: str = PROJECT_ID, location: str = BQ_LOCATION):
        self.client = bigquery.Client(project=project_id, client_options=ClientOptions(quota_project_id=project_id))
        self.location = location

    def run(self, sql: str) -> Dict[str, Any]:
        if not is_select_only(sql):
            return {"error": "Only SELECT queries are allowed."}
        ok, illegal = tables_within_allowlist(sql, ALLOWED_TABLES)
        if not ok:
            return {"error": f"Query references non-allowlisted tables: {', '.join(sorted(illegal))}"}
        job_config = bigquery.QueryJobConfig()
        job_config.use_legacy_sql = False
        job_config.labels = {"agent": "nj_voter_chat"}
        start = time.time()
        query_job = self.client.query(sql, job_config=job_config, location=self.location)
        result_iter = query_job.result(timeout=QUERY_TIMEOUT_SECONDS)
        elapsed = time.time() - start
        rows = []
        for i, r in enumerate(result_iter):
            if i >= MAX_ROWS:
                break
            rows.append(dict(r))
        truncated = query_job.total_rows is not None and query_job.total_rows > len(rows)
        return {"rows": rows, "row_count": len(rows), "truncated": truncated, "elapsed_sec": round(elapsed, 3), "sql": sql}
