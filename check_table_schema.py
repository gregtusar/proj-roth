#!/usr/bin/env python3
"""
Script to check the current BigQuery table schema.
"""

import os
import tempfile
from google.cloud import bigquery

def main():
    credentials_json = os.getenv('GCP_CREDENTIALS')
    if not credentials_json:
        print("No GCP_CREDENTIALS found")
        return
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(credentials_json)
        creds_file = f.name

    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file
        client = bigquery.Client(project='proj-roth')

        table_ref = client.dataset('voter_data').table('voters')
        table = client.get_table(table_ref)

        print('Current table schema:')
        print(f'Total columns: {len(table.schema)}')
        print()
        
        geocoding_columns = ['latitude', 'longitude', 'geocoding_accuracy', 'geocoding_source', 'geocoding_timestamp', 'full_address']
        existing_geocoding_cols = []
        
        for field in table.schema:
            if field.name in geocoding_columns:
                existing_geocoding_cols.append(field.name)
            print(f'  {field.name}: {field.field_type}')
        
        print()
        print(f'Existing geocoding columns: {existing_geocoding_cols}')
        print(f'Missing geocoding columns: {[col for col in geocoding_columns if col not in existing_geocoding_cols]}')

    finally:
        os.unlink(creds_file)

if __name__ == "__main__":
    main()
