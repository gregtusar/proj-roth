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
# or: pip install google-adk
export GOOGLE_CLOUD_PROJECT=proj-roth
export GOOGLE_CLOUD_REGION=us-central1
```

## Run CLI
```
python -m agents.nj_voter_chat_adk.app_cli
```

## Run Interactive CLI
```
python -m agents.nj_voter_chat_adk.app_cli
```

## Deploy to Cloud Run (public URL)
Prereqs:
- You have permissions in project proj-roth and the service account agent-runner@proj-roth.iam.gserviceaccount.com exists.
- gcloud is installed and authenticated.

One-liner:
```
PROJECT_ID=proj-roth REGION=us-central1 bash scripts/deploy_nj_voter_chat.sh
```

This will:
- Build a Docker image from agents/nj_voter_chat_adk/Dockerfile
- Push it to Artifact Registry us-central1
- Deploy Cloud Run service nj-voter-chat with unauthenticated access
- Print the public HTTPS URL

## Guardrails
- SELECT-only SQL
- Allowlist: voters, street_party_summary
- Max rows 10k, 60s timeout

## Test Prompts
- How many voters are registered per party in Somerset County?
- Top 10 streets with highest Democrat concentration in Hunterdon County.
- What is the centroid latitude/longitude of Democratic voters in Union County?
- DROP TABLE voter_data.voters (expect refusal)
