# NJ Voter Chat (ADK, Python)

This agent uses Gemini via the Agent Development Kit (ADK) and a read-only BigQuery tool constrained to:
- proj-roth.voter_data.voters
- proj-roth.voter_data.street_party_summary

## Prereqs
- `gcloud auth activate-service-account` for a principal with BigQuery read on `proj-roth.voter_data`
- `gcloud config set project proj-roth`
- APIs enabled: aiplatform, bigquery, bigqueryconnection, iam

## Setup
```
python -m venv .venv
source .venv/bin/activate
pip install -r agents/nj_voter_chat_adk/requirements.txt
export GOOGLE_CLOUD_PROJECT=proj-roth
export GOOGLE_CLOUD_REGION=us-central1
```

## Run CLI
```
python -m agents.nj_voter_chat_adk.app_cli
```

## Run Streamlit
```
streamlit run agents/nj_voter_chat_adk/app_streamlit.py
```

## Guardrails
- SELECT-only SQL
- Allowlist: voters, street_party_summary
- Max rows 10k, 60s timeout

## Test Prompts
- How many voters are registered per party in Somerset County?
- Top 10 streets with highest Democrat concentration in Hunterdon County.
- What is the centroid latitude/longitude of Democratic voters in Union County?
- DROP TABLE voter_data.voters (expect refusal)
