#!/usr/bin/env python3
"""
Validate the migration was successful.
Checks data integrity, relationships, and geocoding preservation.
"""

import os
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def validate_record_counts(client):
    """Validate record counts across all tables."""
    
    print("=" * 60)
    print("RECORD COUNT VALIDATION")
    print("=" * 60)
    
    tables = [
        'individuals',
        'addresses', 
        'individual_addresses',
        'raw_voters',
        'raw_donations',
        'voters',
        'donations'
    ]
    
    counts = {}
    for table in tables:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{table}`"
        result = list(client.query(query).result())[0]
        counts[table] = result.count
        print(f"{table:25} {result.count:>10,} records")
    
    print("\nValidation checks:")
    
    # Check that we have data
    if counts['voters'] > 0:
        print("✓ Voters table populated")
    else:
        print("✗ Voters table empty!")
    
    if counts['individuals'] > 0:
        print("✓ Individuals extracted")
    else:
        print("✗ No individuals found!")
    
    if counts['addresses'] > 0:
        print("✓ Addresses preserved")
    else:
        print("✗ No addresses found!")
    
    return counts

def validate_geocoding_preservation(client):
    """Ensure geocoding data was preserved."""
    
    print("\n" + "=" * 60)
    print("GEOCODING PRESERVATION VALIDATION")
    print("=" * 60)
    
    # Check geocoded addresses
    query = f"""
    SELECT 
        COUNT(*) as total_addresses,
        COUNTIF(latitude IS NOT NULL AND longitude IS NOT NULL) as geocoded,
        COUNTIF(latitude IS NULL OR longitude IS NULL) as not_geocoded
    FROM `{PROJECT_ID}.{DATASET_ID}.addresses`
    """
    
    result = list(client.query(query).result())[0]
    geocode_rate = result.geocoded / result.total_addresses * 100 if result.total_addresses > 0 else 0
    
    print(f"Total addresses:     {result.total_addresses:>10,}")
    print(f"Geocoded:           {result.geocoded:>10,} ({geocode_rate:.1f}%)")
    print(f"Not geocoded:       {result.not_geocoded:>10,}")
    
    if geocode_rate > 90:
        print("✓ Geocoding well preserved (>90%)")
    elif geocode_rate > 70:
        print("⚠ Geocoding partially preserved (>70%)")
    else:
        print("✗ Geocoding poorly preserved (<70%)")
    
    return geocode_rate

def validate_relationships(client):
    """Validate foreign key relationships."""
    
    print("\n" + "=" * 60)
    print("RELATIONSHIP VALIDATION")
    print("=" * 60)
    
    # Check voter-individual relationships
    query = f"""
    SELECT 
        COUNT(*) as total_voters,
        COUNT(DISTINCT master_id) as unique_individuals,
        COUNT(DISTINCT address_id) as unique_addresses,
        COUNTIF(master_id IS NULL) as missing_individual,
        COUNTIF(address_id IS NULL) as missing_address
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    """
    
    result = list(client.query(query).result())[0]
    
    print("Voter relationships:")
    print(f"  Total voters:        {result.total_voters:>10,}")
    print(f"  Unique individuals:  {result.unique_individuals:>10,}")
    print(f"  Unique addresses:    {result.unique_addresses:>10,}")
    
    if result.missing_individual == 0:
        print("  ✓ All voters linked to individuals")
    else:
        print(f"  ✗ {result.missing_individual:,} voters missing individual link")
    
    if result.missing_address == 0:
        print("  ✓ All voters linked to addresses")
    else:
        print(f"  ✗ {result.missing_address:,} voters missing address link")
    
    # Check donation-individual relationships
    query = f"""
    SELECT 
        COUNT(*) as total_donations,
        COUNTIF(master_id IS NOT NULL) as matched,
        COUNTIF(master_id IS NULL) as unmatched,
        COUNT(DISTINCT master_id) as unique_donors
    FROM `{PROJECT_ID}.{DATASET_ID}.donations`
    """
    
    result = list(client.query(query).result())[0]
    match_rate = result.matched / result.total_donations * 100 if result.total_donations > 0 else 0
    
    print("\nDonation relationships:")
    print(f"  Total donations:     {result.total_donations:>10,}")
    print(f"  Matched to voters:   {result.matched:>10,} ({match_rate:.1f}%)")
    print(f"  Unmatched:          {result.unmatched:>10,}")
    print(f"  Unique donors:       {result.unique_donors:>10,}")

def validate_views(client):
    """Validate that views work correctly."""
    
    print("\n" + "=" * 60)
    print("VIEW VALIDATION")
    print("=" * 60)
    
    views = [
        'voter_geo_view',
        'donor_view',
        'street_party_summary_new',
        'voters_compat'
    ]
    
    for view in views:
        try:
            query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{view}` LIMIT 1"
            result = list(client.query(query).result())[0]
            print(f"✓ {view:30} accessible ({result.count:,} records)")
        except Exception as e:
            print(f"✗ {view:30} ERROR: {str(e)[:50]}")

def validate_data_quality(client):
    """Check data quality metrics."""
    
    print("\n" + "=" * 60)
    print("DATA QUALITY VALIDATION")
    print("=" * 60)
    
    # Check party distribution
    query = f"""
    SELECT 
        demo_party,
        COUNT(*) as voter_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    GROUP BY demo_party
    ORDER BY voter_count DESC
    LIMIT 5
    """
    
    print("\nParty distribution:")
    results = client.query(query).result()
    for row in results:
        party = row.demo_party or 'NULL'
        print(f"  {party:20} {row.voter_count:>8,} ({row.pct:>5.1f}%)")
    
    # Check county distribution
    query = f"""
    SELECT 
        county_name,
        COUNT(*) as voter_count
    FROM `{PROJECT_ID}.{DATASET_ID}.voters`
    WHERE county_name IS NOT NULL
    GROUP BY county_name
    ORDER BY voter_count DESC
    """
    
    print("\nCounty distribution:")
    results = client.query(query).result()
    for row in results:
        print(f"  {row.county_name:20} {row.voter_count:>8,}")

def main():
    """Run all validation checks."""
    print(f"\nMIGRATION VALIDATION REPORT")
    print(f"Generated: {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}\n")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Run all validations
    counts = validate_record_counts(client)
    geocode_rate = validate_geocoding_preservation(client)
    validate_relationships(client)
    validate_views(client)
    validate_data_quality(client)
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    if counts['voters'] == 0:
        issues.append("Voters table is empty")
    if counts['addresses'] == 0:
        issues.append("No addresses preserved")
    if geocode_rate < 70:
        issues.append("Poor geocoding preservation")
    elif geocode_rate < 90:
        warnings.append("Partial geocoding preservation")
    
    if issues:
        print("\n❌ CRITICAL ISSUES:")
        for issue in issues:
            print(f"   - {issue}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not issues and not warnings:
        print("\n✅ ALL VALIDATIONS PASSED!")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()