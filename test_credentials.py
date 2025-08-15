#!/usr/bin/env python3
import os
import json
import tempfile
from google.cloud import bigquery

credentials_json = os.getenv('GCP_CREDENTIALS')
if not credentials_json:
    print("No GCP_CREDENTIALS found")
    exit(1)

print(f"Credentials length: {len(credentials_json)}")

try:
    creds_data = json.loads(credentials_json)
    print("✅ JSON parsing successful")
    print(f"Project ID: {creds_data.get('project_id')}")
    print(f"Client email: {creds_data.get('client_email')}")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(credentials_json)
        creds_file = f.name
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file
    client = bigquery.Client(project='proj-roth')
    
    datasets = list(client.list_datasets())
    print(f"✅ BigQuery client works. Found {len(datasets)} datasets")
    
    os.unlink(creds_file)
    
except Exception as e:
    print(f"❌ Error: {e}")
