#!/usr/bin/env python3
"""
Simple direct matching of voters to individuals.
Uses the existing mappings we created during individual extraction.
"""

import os
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def match_voters_simple(client):
    """Direct match of voters using the same logic as individual extraction."""
    
    print("Matching voters to individuals using direct mapping...")
    
    # Use a simpler approach - directly map based on how we created individuals
    query = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.voters`
    SELECT
        GENERATE_UUID() as voter_record_id,
        rv.id as vendor_voter_id,
        -- Match to individual using same logic as extraction
        SUBSTR(TO_HEX(SHA256(CONCAT(
            UPPER(CONCAT(
                COALESCE(rv.name_last, ''), ', ',
                COALESCE(rv.name_first, ''), ' ',
                COALESCE(rv.name_middle, '')
            )), '|',
            TO_HEX(SHA256(UPPER(CONCAT(
                COALESCE(CAST(rv.addr_residential_street_number AS STRING), ''), ' ',
                COALESCE(rv.addr_residential_street_name, ''), ', ',
                COALESCE(rv.addr_residential_city, ''), ', ',
                COALESCE(rv.addr_residential_state, ''), ' ',
                COALESCE(rv.addr_residential_zip_code, '')
            ))))
        ))), 1, 16) as master_id,
        -- Match to address using same logic
        SUBSTR(TO_HEX(SHA256(UPPER(CONCAT(
            COALESCE(CAST(rv.addr_residential_street_number AS STRING), ''), ' ',
            COALESCE(rv.addr_residential_street_name, ''), ', ',
            COALESCE(rv.addr_residential_city, ''), ', ',
            COALESCE(rv.addr_residential_state, ''), ' ',
            COALESCE(rv.addr_residential_zip_code, '')
        )))), 1, 16) as address_id,
        
        -- Copy all other fields
        rv.demo_party,
        rv.demo_age,
        rv.demo_race,
        rv.demo_race_confidence,
        rv.demo_gender,
        rv.registration_status_civitech as registration_status,
        rv.voter_type,
        rv.congressional_name as congressional_district,
        rv.state_house_name as state_house_district,
        rv.state_senate_name as state_senate_district,
        rv.precinct_name as precinct,
        rv.municipal_name,
        rv.county_name,
        rv.city_council_name as city_council_district,
        rv.score_support_generic_dem,
        rv.current_support_score,
        
        -- Voting history
        rv.participation_primary_2016,
        rv.participation_primary_2017,
        rv.participation_primary_2018,
        rv.participation_primary_2019,
        rv.participation_primary_2020,
        rv.participation_primary_2021,
        rv.participation_primary_2022,
        rv.participation_primary_2023,
        rv.participation_primary_2024,
        rv.participation_general_2016,
        rv.participation_general_2017,
        rv.participation_general_2018,
        rv.participation_general_2019,
        rv.participation_general_2020,
        rv.participation_general_2021,
        rv.participation_general_2022,
        rv.participation_general_2023,
        rv.participation_general_2024,
        
        -- Vote columns
        rv.vote_primary_dem_2016,
        rv.vote_primary_rep_2016,
        rv.vote_primary_dem_2017,
        rv.vote_primary_rep_2017,
        rv.vote_primary_dem_2018,
        rv.vote_primary_rep_2018,
        rv.vote_primary_dem_2019,
        rv.vote_primary_rep_2019,
        rv.vote_primary_dem_2020,
        rv.vote_primary_rep_2020,
        rv.vote_primary_dem_2021,
        rv.vote_primary_rep_2021,
        rv.vote_primary_dem_2022,
        rv.vote_primary_rep_2022,
        rv.vote_primary_dem_2023,
        rv.vote_primary_rep_2023,
        rv.vote_primary_dem_2024,
        rv.vote_primary_rep_2024,
        
        rv.email,
        rv.phone_1,
        rv.phone_2,
        
        CURRENT_TIMESTAMP() as created_at,
        CURRENT_TIMESTAMP() as updated_at
        
    FROM `{PROJECT_ID}.{DATASET_ID}.raw_voters` rv
    WHERE rv.name_last IS NOT NULL
    """
    
    print("Executing simplified match query...")
    query_job = client.query(query)
    query_job.result()
    
    # Get statistics
    stats_query = f"""
    SELECT 
        COUNT(*) as total_matched,
        COUNT(DISTINCT vendor_voter_id) as unique_voters,
        COUNT(DISTINCT master_id) as unique_individuals
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    """
    
    stats = client.query(stats_query).result()
    for row in stats:
        print(f"\nMatch Results:")
        print(f"  Total records: {row.total_matched:,}")
        print(f"  Unique voters: {row.unique_voters:,}")
        print(f"  Unique individuals: {row.unique_individuals:,}")
        return row.total_matched

def main():
    """Main execution."""
    print(f"Starting simplified voter matching at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Clear existing
    print("Clearing existing voters table...")
    client.query(f"TRUNCATE TABLE `{PROJECT_ID}.{DATASET_ID}.voters`").result()
    
    # Run matching
    count = match_voters_simple(client)
    
    print(f"\n✓ Voter matching completed!")
    print(f"  Processed: {count:,} records")

if __name__ == "__main__":
    main()