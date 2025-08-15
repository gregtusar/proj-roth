#!/usr/bin/env python3
"""
Quick check of geocoding progress and test mapping framework.
"""

import os
import tempfile
from google.cloud import bigquery

def main():
    credentials_json = os.getenv('GCP_CREDENTIALS')
    if not credentials_json:
        print("No GCP_CREDENTIALS found")
        return False
    
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
        total = int(result.iloc[0]["total_voters"])
        geocoded = int(result.iloc[0]["geocoded_voters"])
        percentage = float(result.iloc[0]["geocoded_percentage"])
        
        print(f'🗺️  Geocoding Progress: {geocoded:,} / {total:,} ({percentage}%)')

        if geocoded > 0:
            sample_query = '''
            SELECT voter_id, party_affiliation, county, latitude, longitude
            FROM `proj-roth.voter_data.voters`
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            LIMIT 5
            '''

            sample_result = client.query(sample_query).to_dataframe()
            print('\nSample geocoded voters:')
            for _, row in sample_result.iterrows():
                print(f'  {row["voter_id"]}: {row["party_affiliation"]} in {row["county"]} at ({row["latitude"]:.4f}, {row["longitude"]:.4f})')
        
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'creds_file' in locals():
            os.unlink(creds_file)

if __name__ == "__main__":
    main()
