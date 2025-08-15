#!/usr/bin/env python3
"""
Check the progress of the geocoding pipeline.
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

        query = '''
        SELECT 
            COUNT(*) as total_voters,
            COUNT(latitude) as geocoded_voters,
            ROUND(COUNT(latitude) * 100.0 / COUNT(*), 2) as geocoded_percentage
        FROM `proj-roth.voter_data.voters`
        '''

        result = client.query(query).to_dataframe()
        print('🗺️  Geocoding Progress Report')
        print('=' * 40)
        print(f'Total voters: {result.iloc[0]["total_voters"]:,}')
        print(f'Geocoded voters: {result.iloc[0]["geocoded_voters"]:,}')
        print(f'Geocoded percentage: {result.iloc[0]["geocoded_percentage"]}%')
        
        street_query = '''
        SELECT COUNT(*) as street_count
        FROM `proj-roth.voter_data.street_party_summary`
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        '''
        
        street_result = client.query(street_query).to_dataframe()
        print(f'Geocoded streets: {street_result.iloc[0]["street_count"]:,}')

    finally:
        os.unlink(creds_file)

if __name__ == "__main__":
    main()
