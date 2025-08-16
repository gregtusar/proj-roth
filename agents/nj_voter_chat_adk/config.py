import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
DATASET = os.getenv("VOTER_DATASET", "voter_data")
ALLOWED_TABLES = {
    f"{PROJECT_ID}.{DATASET}.voters",
    f"{PROJECT_ID}.{DATASET}.street_party_summary",
}
MAX_ROWS = int(os.getenv("BQ_MAX_ROWS", "10000"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("BQ_QUERY_TIMEOUT_SECONDS", "60"))
MODEL = os.getenv("ADK_MODEL", "gemini-1.5-pro")
SYSTEM_PROMPT = os.getenv(
    "ADK_SYSTEM_PROMPT",
    "You are a data assistant for NJ voter data. Use the BigQuery tool to answer questions by generating minimal, correct SQL against approved tables (voter_data.voters and voter_data.street_party_summary). Only run read-only SELECT queries. Do not access tables outside the allowlist. If asked to perform writes or access restricted info, refuse and explain.",
)
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
