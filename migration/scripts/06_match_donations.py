#!/usr/bin/env python3
"""
Match donations to individuals using fuzzy name matching.
Links donation records to master_ids where possible.
"""

import os
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def match_donations_to_individuals(client):
    """Match donations to individuals using name matching."""
    
    print("Matching donations to individuals...")
    
    # Match donations to individuals using LEFT JOINs
    query = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.donations`
    WITH matched_donors AS (
        SELECT 
            rd.*,
            i.master_id,
            ROW_NUMBER() OVER (
                PARTITION BY rd.full_name 
                ORDER BY i.master_id
            ) as rn
        FROM `{PROJECT_ID}.{DATASET_ID}.raw_donations` rd
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individuals` i
        ON UPPER(i.name_first) = UPPER(rd.first_name)
        AND UPPER(i.name_last) = UPPER(rd.last_name)
        WHERE rd.last_name IS NOT NULL
    )
    SELECT
        GENERATE_UUID() as donation_record_id,
        master_id,
        CAST(NULL AS STRING) as address_id,  -- Simplify for now
        
        -- Donation details
        committee_name,
        contribution_amount,
        election_type,
        election_year,
        employer,
        occupation,
        CAST(NULL AS DATE) as donation_date,
        
        -- Original data
        full_name as original_full_name,
        CONCAT(address_1, ', ', city, ', ', state, ' ', zip) as original_address,
        
        -- Match confidence
        CASE 
            WHEN master_id IS NOT NULL THEN 0.9
            ELSE 0.0
        END as match_confidence,
        
        CASE 
            WHEN master_id IS NOT NULL THEN 'exact_name_match'
            ELSE 'no_match'
        END as match_method,
        
        CURRENT_TIMESTAMP() as created_at
        
    FROM matched_donors
    WHERE rn = 1 OR master_id IS NULL
    """
    
    print("Executing donation match query...")
    query_job = client.query(query)
    query_job.result()
    
    # Get statistics
    stats_query = f"""
    SELECT 
        COUNT(*) as total_donations,
        COUNTIF(master_id IS NOT NULL) as matched_donations,
        COUNTIF(master_id IS NULL) as unmatched_donations,
        AVG(match_confidence) as avg_confidence,
        SUM(contribution_amount) as total_contributions
    FROM `{PROJECT_ID}.{DATASET_ID}.donations`
    """
    
    stats = client.query(stats_query).result()
    for row in stats:
        print(f"\nDonation Match Results:")
        print(f"  Total donations: {row.total_donations:,}")
        print(f"  Matched to voters: {row.matched_donations:,}")
        print(f"  Unmatched: {row.unmatched_donations:,}")
        print(f"  Average confidence: {row.avg_confidence:.2f}")
        print(f"  Total contributions: ${row.total_contributions:,.2f}")
        return row.total_donations

def analyze_donor_voters(client):
    """Analyze overlap between donors and voters."""
    
    print("\nAnalyzing donor-voter overlap...")
    
    query = f"""
    SELECT 
        COUNT(DISTINCT d.master_id) as unique_donors,
        COUNT(DISTINCT CASE WHEN v.master_id IS NOT NULL THEN d.master_id END) as donors_who_vote,
        COUNT(DISTINCT v.master_id) as total_voters
    FROM `{PROJECT_ID}.{DATASET_ID}.donations` d
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.voters` v
    ON d.master_id = v.master_id
    """
    
    results = client.query(query).result()
    for row in results:
        print(f"  Unique donors: {row.unique_donors:,}")
        print(f"  Donors who are voters: {row.donors_who_vote:,}")
        print(f"  Match rate: {row.donors_who_vote/row.unique_donors*100:.1f}%")

def main():
    """Main execution."""
    print(f"Starting donation matching at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Clear existing
    print("Clearing existing donations table...")
    client.query(f"TRUNCATE TABLE `{PROJECT_ID}.{DATASET_ID}.donations`").result()
    
    # Run matching
    count = match_donations_to_individuals(client)
    
    # Analyze overlap
    analyze_donor_voters(client)
    
    print(f"\n✓ Donation matching completed!")
    print(f"  Processed: {count:,} records")

if __name__ == "__main__":
    main()