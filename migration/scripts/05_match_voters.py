#!/usr/bin/env python3
"""
Match raw voters to individuals and populate the processed voters table.
Links each voter record to a master_id and address_id.
"""

import os
import uuid
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def match_voters_to_individuals(client):
    """Match voters to individuals using name and address."""
    
    print("Matching voters to individuals and addresses...")
    
    # Create the processed voters table by joining raw_voters with individuals and addresses
    query = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.voters`
    SELECT
        -- Generate voter_record_id
        GENERATE_UUID() as voter_record_id,
        rv.id as vendor_voter_id,
        i.master_id,
        a.address_id,
        
        -- Demographics
        rv.demo_party,
        rv.demo_age,
        rv.demo_race,
        rv.demo_race_confidence,
        rv.demo_gender,
        
        -- Registration
        rv.registration_status_civitech as registration_status,
        rv.voter_type,
        
        -- Districts
        rv.congressional_name as congressional_district,
        rv.state_house_name as state_house_district,
        rv.state_senate_name as state_senate_district,
        rv.precinct_name as precinct,
        rv.municipal_name,
        rv.county_name,
        rv.city_council_name as city_council_district,
        
        -- Scores
        rv.score_support_generic_dem,
        rv.current_support_score,
        
        -- Voting History
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
        
        -- Contact info
        rv.email,
        rv.phone_1,
        rv.phone_2,
        
        -- Metadata
        CURRENT_TIMESTAMP() as created_at,
        CURRENT_TIMESTAMP() as updated_at
        
    FROM `{PROJECT_ID}.{DATASET_ID}.raw_voters` rv
    
    -- Join to individuals through the individual_addresses table for accurate matching
    INNER JOIN (
        SELECT DISTINCT
            i.master_id,
            i.standardized_name,
            i.name_first,
            i.name_last,
            ia.address_id
        FROM `{PROJECT_ID}.{DATASET_ID}.individuals` i
        JOIN `{PROJECT_ID}.{DATASET_ID}.individual_addresses` ia
        ON i.master_id = ia.master_id
    ) ind
    ON UPPER(COALESCE(rv.name_first, '')) = UPPER(COALESCE(ind.name_first, ''))
    AND UPPER(COALESCE(rv.name_last, '')) = UPPER(COALESCE(ind.name_last, ''))
    
    -- Join to addresses to verify address match
    INNER JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a
    ON ind.address_id = a.address_id
    AND UPPER(COALESCE(rv.addr_residential_street_name, '')) = UPPER(COALESCE(a.street_name, ''))
    AND UPPER(COALESCE(CAST(rv.addr_residential_street_number AS STRING), '')) = UPPER(COALESCE(a.street_number, ''))
    """
    
    print("Executing match query...")
    query_job = client.query(query)
    query_job.result()
    
    # Get match statistics
    stats_query = f"""
    SELECT 
        COUNT(*) as total_voters,
        COUNTIF(master_id IS NOT NULL) as matched_voters,
        COUNTIF(master_id IS NULL) as unmatched_voters
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    """
    
    stats = client.query(stats_query).result()
    for row in stats:
        print(f"\nMatch Results:")
        print(f"  Total voters: {row.total_voters:,}")
        print(f"  Matched: {row.matched_voters:,}")
        print(f"  Unmatched: {row.unmatched_voters:,}")
    
    return row.total_voters

def verify_voter_matching(client):
    """Verify the voter matching process."""
    
    print("\nVerifying voter matching...")
    
    # Check original voter count
    original_query = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.raw_voters`
    """
    
    original_count = list(client.query(original_query).result())[0].count
    
    # Check matched voter count
    matched_query = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    """
    
    matched_count = list(client.query(matched_query).result())[0].count
    
    # Check distribution by party
    party_query = f"""
    SELECT 
        demo_party,
        COUNT(*) as voter_count
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    GROUP BY demo_party
    ORDER BY voter_count DESC
    """
    
    print(f"  Original raw voters: {original_count:,}")
    print(f"  Matched voters: {matched_count:,}")
    print(f"  Match rate: {matched_count/original_count*100:.1f}%")
    
    print("\n  Party distribution:")
    party_results = client.query(party_query).result()
    for row in party_results:
        print(f"    {row.demo_party or 'NULL'}: {row.voter_count:,}")
    
    return matched_count

def main():
    """Main matching process."""
    print(f"Starting voter matching at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Clear existing voters table
    print("Clearing existing voters table...")
    truncate_query = f"TRUNCATE TABLE `{PROJECT_ID}.{DATASET_ID}.voters`"
    client.query(truncate_query).result()
    
    # Match voters to individuals
    voter_count = match_voters_to_individuals(client)
    
    # Verify matching
    verify_voter_matching(client)
    
    print(f"\nVoter matching completed successfully!")
    print(f"  Processed voters: {voter_count:,}")

if __name__ == "__main__":
    main()