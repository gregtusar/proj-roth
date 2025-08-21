#!/usr/bin/env python3
"""
Fix Bernardsville donor matching issue.
The donations exist but weren't matched to addresses properly.
"""

import os
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def fix_bernardsville_matching(client):
    """Match Bernardsville donors to addresses and individuals."""
    
    print("Fixing Bernardsville donor matching...")
    
    # First, let's see what Bernardsville donations we have
    query = f"""
    SELECT 
        original_full_name,
        original_address,
        COUNT(*) as donation_count,
        SUM(contribution_amount) as total_amount
    FROM `{PROJECT_ID}.{DATASET_ID}.donations`
    WHERE UPPER(original_address) LIKE '%BERNARDSVILLE%'
    AND master_id IS NULL  -- Not matched yet
    GROUP BY original_full_name, original_address
    ORDER BY total_amount DESC
    """
    
    unmatched = list(client.query(query).result())
    print(f"Found {len(unmatched)} unmatched Bernardsville donors")
    
    if not unmatched:
        print("No unmatched Bernardsville donors found")
        return
    
    # Now let's try to match them
    print("\nAttempting to match donors to voters...")
    
    update_query = f"""
    -- Update donations with Bernardsville addresses to match voters
    UPDATE `{PROJECT_ID}.{DATASET_ID}.donations` d
    SET 
        d.master_id = v.master_id,
        d.address_id = v.address_id,
        d.match_confidence = 0.8,
        d.match_method = 'city_name_match'
    FROM (
        SELECT DISTINCT
            i.master_id,
            v.address_id,
            i.name_first,
            i.name_last,
            a.city
        FROM `{PROJECT_ID}.{DATASET_ID}.voters` v
        JOIN `{PROJECT_ID}.{DATASET_ID}.individuals` i ON v.master_id = i.master_id
        JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a ON v.address_id = a.address_id
        WHERE UPPER(a.city) = 'BERNARDSVILLE'
    ) v
    WHERE d.master_id IS NULL
    AND UPPER(d.original_address) LIKE '%BERNARDSVILLE%'
    AND (
        -- Try to match on last name (fuzzy match)
        UPPER(SPLIT(d.original_full_name, ',')[OFFSET(0)]) = UPPER(v.name_last)
        OR UPPER(SPLIT(d.original_full_name, ' ')[OFFSET(0)]) = UPPER(v.name_last)
    )
    """
    
    job = client.query(update_query)
    result = job.result()
    
    print(f"Updated {job.num_dml_affected_rows} donation records")
    
    # Refresh materialized views
    print("\nRefreshing materialized views...")
    
    # Refresh donor_view (it's a regular view, so automatic)
    # Refresh major_donors view
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.major_donors` AS
    SELECT 
        master_id,
        standardized_name,
        city,
        voter_party,
        SUM(contribution_amount) as total_contributed,
        COUNT(*) as donation_count,
        MAX(contribution_amount) as max_contribution,
        STRING_AGG(DISTINCT committee_name LIMIT 5) as committees
    FROM `{PROJECT_ID}.{DATASET_ID}.donor_view`
    WHERE master_id IS NOT NULL
    GROUP BY master_id, standardized_name, city, voter_party
    HAVING SUM(contribution_amount) > 1000
    ORDER BY total_contributed DESC
    """
    
    job = client.query(query)
    job.result()
    print("✓ Refreshed major_donors view")
    
    # Check results
    query = f"""
    SELECT COUNT(*) as donor_count
    FROM `{PROJECT_ID}.{DATASET_ID}.donor_view`
    WHERE UPPER(city) = 'BERNARDSVILLE'
    AND master_id IS NOT NULL
    """
    
    result = list(client.query(query).result())[0]
    print(f"\n✓ Now have {result.donor_count} matched donors in Bernardsville")

def main():
    """Run the fix."""
    print("BERNARDSVILLE DONOR MATCHING FIX")
    print("=" * 60)
    
    client = bigquery.Client(project=PROJECT_ID)
    fix_bernardsville_matching(client)
    
    print("\n" + "=" * 60)
    print("FIX COMPLETE")
    print("Bernardsville donors should now appear in queries")

if __name__ == "__main__":
    main()