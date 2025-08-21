#!/usr/bin/env python3
"""
Fix voter-individual matching by using consistent ID generation.
This recreates the voters table with proper master_id and address_id linking.
"""

import os
import hashlib
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def fix_voter_matching(client):
    """Re-match voters using the same ID generation as individuals."""
    
    print("Fixing voter-individual matching with consistent IDs...")
    
    # First, let's understand how individuals were created
    # They used: SHA256(standardized_name + '|' + address_id)[:16]
    # Where standardized_name = "LAST, FIRST MIDDLE"
    # And address_id = SHA256(standardized_address)[:16]
    
    # Recreate voters table with proper matching
    query = f"""
    -- Clear and repopulate voters table with correct IDs
    TRUNCATE TABLE `{PROJECT_ID}.{DATASET_ID}.voters`;
    
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.voters`
    WITH voter_addresses AS (
        -- Generate address IDs matching the addresses table
        SELECT 
            rv.*,
            SUBSTR(TO_HEX(SHA256(UPPER(CONCAT(
                COALESCE(CAST(rv.addr_residential_street_number AS STRING), ''), ' ',
                COALESCE(rv.addr_residential_street_name, ''), ', ',
                COALESCE(rv.addr_residential_city, ''), ', ',
                COALESCE(rv.addr_residential_state, ''), ' ',
                COALESCE(rv.addr_residential_zip_code, '')
            )))), 1, 16) as computed_address_id
        FROM `{PROJECT_ID}.{DATASET_ID}.raw_voters` rv
    ),
    voter_individuals AS (
        -- Generate individual IDs matching the individuals table
        SELECT 
            va.*,
            a.address_id as matched_address_id,
            -- Create standardized name in same format as individuals table
            UPPER(CONCAT(
                COALESCE(va.name_last, ''), ', ',
                COALESCE(va.name_first, ''), ' ',
                COALESCE(va.name_middle, '')
            )) as standardized_name,
            -- Generate master_id using standardized_name + address_id
            SUBSTR(TO_HEX(SHA256(CONCAT(
                UPPER(CONCAT(
                    COALESCE(va.name_last, ''), ', ',
                    COALESCE(va.name_first, ''), ' ',
                    COALESCE(va.name_middle, '')
                )), '|',
                COALESCE(a.address_id, 'NO_ADDR')
            ))), 1, 16) as computed_master_id
        FROM voter_addresses va
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a
        ON va.computed_address_id = a.address_id
    )
    SELECT
        GENERATE_UUID() as voter_record_id,
        vi.id as vendor_voter_id,
        -- Use the matched individual's master_id if it exists, otherwise use computed
        COALESCE(i.master_id, vi.computed_master_id) as master_id,
        -- Use matched address_id
        COALESCE(vi.matched_address_id, vi.computed_address_id) as address_id,
        
        -- All other fields
        vi.demo_party,
        vi.demo_age,
        vi.demo_race,
        vi.demo_race_confidence,
        vi.demo_gender,
        vi.registration_status_civitech as registration_status,
        vi.voter_type,
        vi.congressional_name as congressional_district,
        vi.state_house_name as state_house_district,
        vi.state_senate_name as state_senate_district,
        vi.precinct_name as precinct,
        vi.municipal_name,
        vi.county_name,
        vi.city_council_name as city_council_district,
        vi.score_support_generic_dem,
        vi.current_support_score,
        
        -- Voting history
        vi.participation_primary_2016,
        vi.participation_primary_2017,
        vi.participation_primary_2018,
        vi.participation_primary_2019,
        vi.participation_primary_2020,
        vi.participation_primary_2021,
        vi.participation_primary_2022,
        vi.participation_primary_2023,
        vi.participation_primary_2024,
        vi.participation_general_2016,
        vi.participation_general_2017,
        vi.participation_general_2018,
        vi.participation_general_2019,
        vi.participation_general_2020,
        vi.participation_general_2021,
        vi.participation_general_2022,
        vi.participation_general_2023,
        vi.participation_general_2024,
        
        -- Vote columns
        vi.vote_primary_dem_2016,
        vi.vote_primary_rep_2016,
        vi.vote_primary_dem_2017,
        vi.vote_primary_rep_2017,
        vi.vote_primary_dem_2018,
        vi.vote_primary_rep_2018,
        vi.vote_primary_dem_2019,
        vi.vote_primary_rep_2019,
        vi.vote_primary_dem_2020,
        vi.vote_primary_rep_2020,
        vi.vote_primary_dem_2021,
        vi.vote_primary_rep_2021,
        vi.vote_primary_dem_2022,
        vi.vote_primary_rep_2022,
        vi.vote_primary_dem_2023,
        vi.vote_primary_rep_2023,
        vi.vote_primary_dem_2024,
        vi.vote_primary_rep_2024,
        
        vi.email,
        vi.phone_1,
        vi.phone_2,
        
        CURRENT_TIMESTAMP() as created_at,
        CURRENT_TIMESTAMP() as updated_at
        
    FROM voter_individuals vi
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individuals` i
    ON vi.standardized_name = i.standardized_name
    WHERE vi.name_last IS NOT NULL
    """
    
    print("Executing fixed matching query...")
    query_job = client.query(query)
    query_job.result()
    
    print("Match complete. Checking results...")

def verify_matching(client):
    """Verify the matching worked correctly."""
    
    # Check how many voters matched to individuals
    query = f"""
    SELECT 
        COUNT(*) as total_voters,
        COUNT(DISTINCT v.master_id) as unique_masters_in_voters,
        COUNT(DISTINCT i.master_id) as matched_individuals,
        COUNT(DISTINCT v.vendor_voter_id) as unique_voter_ids
    FROM `{PROJECT_ID}.{DATASET_ID}.voters` v
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individuals` i
    ON v.master_id = i.master_id
    """
    
    result = list(client.query(query).result())[0]
    
    print(f"\nMatching Results:")
    print(f"  Total voter records:     {result.total_voters:,}")
    print(f"  Unique voters:           {result.unique_voter_ids:,}")
    print(f"  Unique master_ids:       {result.unique_masters_in_voters:,}")
    print(f"  Matched to individuals:  {result.matched_individuals:,}")
    
    # Check if views now work
    query = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.voter_geo_view`
    """
    
    view_count = list(client.query(query).result())[0].count
    print(f"\n  voter_geo_view records:  {view_count:,}")
    
    if view_count > 0:
        print("  ✓ Views are now working!")
    else:
        print("  ✗ Views still not working - checking why...")
        
        # Debug query
        debug_query = f"""
        SELECT 
            'voters' as source,
            COUNT(DISTINCT master_id) as unique_ids,
            MIN(master_id) as sample_id
        FROM `{PROJECT_ID}.{DATASET_ID}.voters`
        UNION ALL
        SELECT 
            'individuals' as source,
            COUNT(DISTINCT master_id) as unique_ids,
            MIN(master_id) as sample_id
        FROM `{PROJECT_ID}.{DATASET_ID}.individuals`
        """
        
        print("\n  Debug - Master ID comparison:")
        debug_results = client.query(debug_query).result()
        for row in debug_results:
            print(f"    {row.source:12} {row.unique_ids:,} unique IDs, sample: {row.sample_id}")
    
    return view_count

def main():
    """Main execution."""
    print(f"Starting voter matching fix at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Fix the matching
    fix_voter_matching(client)
    
    # Verify it worked
    view_count = verify_matching(client)
    
    if view_count > 0:
        print(f"\n✅ SUCCESS! Voter-individual matching fixed.")
        print(f"   {view_count:,} records now available in voter_geo_view")
    else:
        print(f"\n⚠️  Matching improved but views still need work.")

if __name__ == "__main__":
    main()