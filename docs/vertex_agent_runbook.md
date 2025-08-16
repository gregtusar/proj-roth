# Vertex AI Agent Builder: NJ Voter Data Chat

This runbook documents the setup and usage of a Vertex AI Agent Builder chat agent that can answer questions against the BigQuery tables:
- proj-roth.voter_data.voters
- proj-roth.voter_data.street_party_summary

Region: us-central1  
Project: proj-roth  
Model: gemini-1.5-pro  
Agent Name: nj-voter-chat  
Service Account (runtime): agent-runner@proj-roth.iam.gserviceaccount.com

## Architecture

- Vertex AI Agent Builder agent powered by Gemini
- BigQuery Tool scoped to dataset voter_data with table allowlist:
  - voters
  - street_party_summary
- Least-privilege service account used as the agent runtime identity
- Read-only SQL enforced by policy and allowlisting

## Guardrails and Policies

- Queries must be SELECT-only. No DML/DDL.
- Only the approved tables in proj-roth.voter_data are accessible.
- Responses should be based on executed queries; avoid fabricating data.
- If asked for disallowed access or write operations, refuse politely.

Recommended limits:
- Max rows per query: 10k
- Query timeout: 60 seconds

Optional governance:
- Create restricted views (e.g., voters_safe, street_party_summary_safe) and allowlist those instead of base tables.

## IAM

Service account: agent-runner@proj-roth.iam.gserviceaccount.com

Project-level roles:
- roles/aiplatform.user
- roles/bigquery.jobUser

Dataset-level (voter_data):
- roles/bigquery.dataViewer (granted via dataset ACL)

## Required APIs

- aiplatform.googleapis.com
- bigquery.googleapis.com
- bigqueryconnection.googleapis.com

## Verification Commands

Set project and region:
- gcloud config set project proj-roth
- export REGION=us-central1

Enable services:
- gcloud services enable aiplatform.googleapis.com bigquery.googleapis.com bigqueryconnection.googleapis.com

Inspect IAM:
- gcloud projects get-iam-policy proj-roth

Check BigQuery tables:
- bq show --format=prettyjson proj-roth:voter_data.voters
- bq show --format=prettyjson proj-roth:voter_data.street_party_summary

List and describe the agent:
- gcloud alpha aiplatform agents list --project=proj-roth --location=$REGION
- gcloud alpha aiplatform agents describe nj-voter-chat --project=proj-roth --location=$REGION

## Example Prompts

- How many voters are registered per party in Somerset County?
- Top 10 streets with highest Democrat concentration in Hunterdon County.
- What is the centroid latitude/longitude of Democratic voters in Union County?
- Show a breakdown of party counts by county.

The agent should generate SQL that references only:
- proj-roth.voter_data.voters
- proj-roth.voter_data.street_party_summary

and uses only SELECT.

## Suggested SQL Patterns

Party counts by county:
- SELECT county_name, demo_party, COUNT(*) AS c
  FROM `proj-roth.voter_data.voters`
  GROUP BY county_name, demo_party
  ORDER BY county_name, c DESC;

Top streets by Democrat concentration:
- SELECT addr_residential_street_name, county_name, total_voters, democrat_pct
  FROM `proj-roth.voter_data.street_party_summary`
  WHERE county_name = @county
  ORDER BY democrat_pct DESC
  LIMIT 10;

Centroid of voters by party and county:
- SELECT
    demo_party,
    county_name,
    ST_Y(ST_CENTROID(ST_UNION_AGG(location))) AS centroid_lat,
    ST_X(ST_CENTROID(ST_UNION_AGG(location))) AS centroid_lng
  FROM `proj-roth.voter_data.voters`
  WHERE location IS NOT NULL
  GROUP BY demo_party, county_name;

## Operational Notes

- Use the Agent Builder chat preview to validate prompts and results.
- Confirm the SQL shown references only allowlisted tables and SELECT-only statements.
- Monitor Vertex AI logs and BigQuery audit logs for query history under the agent-runner principal.

## Maintenance

- To change guardrails, edit the agent’s system instructions in Agent Builder.
- To restrict data further, create and allowlist views.
## ADK Alternative (Python)

If Console-based Agent Builder is unavailable, use the Python Agent Development Kit (ADK).

Location:
- agents/nj_voter_chat_adk/

Run locally:
- python -m venv .venv && source .venv/bin/activate
- pip install -r agents/nj_voter_chat_adk/requirements.txt
- gcloud auth activate-service-account --key-file /path/to/key.json
- gcloud config set project proj-roth
- export GOOGLE_CLOUD_PROJECT=proj-roth
- export GOOGLE_CLOUD_REGION=us-central1
- streamlit run agents/nj_voter_chat_adk/app_streamlit.py
- Or: python -m agents.nj_voter_chat_adk.app_cli

Guardrails:
- SELECT-only enforced
- Allowlist: proj-roth.voter_data.{voters,street_party_summary}
- Max rows 10k, 60s timeout

Verification:
- Ask the four prompts listed above and confirm refusal on prohibited DDL/DML.

- To rotate credentials, update the service account bindings; no code changes are required.
