#!/usr/bin/env python3
"""
Extract and preserve existing geocoding data from voters table.
This data is expensive to regenerate and must be preserved.
"""

import os
import hashlib
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def standardize_address(street_number, street_name, city, state, zip_code):
    """Create standardized address format."""
    parts = []
    if street_number:
        parts.append(str(street_number).strip())
    if street_name:
        parts.append(street_name.strip().upper())
    
    street = ' '.join(parts) if parts else ''
    
    city = city.strip().upper() if city else ''
    state = state.strip().upper() if state else ''
    zip_code = str(zip_code).strip()[:5] if zip_code else ''
    
    return f"{street}, {city}, {state} {zip_code}".strip(' ,')

def generate_address_id(standardized_address):
    """Generate deterministic address_id from standardized address."""
    return hashlib.sha256(standardized_address.encode()).hexdigest()[:16]

def extract_geocoding_data(client):
    """Extract unique addresses with geocoding from existing voters table."""
    
    print("Extracting geocoded addresses from voters table...")
    
    # Query to extract unique addresses with geocoding
    query = """
    WITH unique_addresses AS (
        SELECT DISTINCT
            addr_residential_street_number,
            addr_residential_street_name,
            addr_residential_city AS city,
            addr_residential_state AS state,
            addr_residential_zip_code AS zip_code,
            county_name AS county,
            latitude,
            longitude,
            COUNT(*) as voter_count
        FROM `proj-roth.voter_data.voters`
        WHERE latitude IS NOT NULL 
          AND longitude IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8
    )
    SELECT 
        addr_residential_street_number,
        addr_residential_street_name,
        city,
        state,
        zip_code,
        county,
        latitude,
        longitude,
        voter_count
    FROM unique_addresses
    ORDER BY county, city, addr_residential_street_name
    """
    
    print("Running extraction query...")
    query_job = client.query(query)
    results = query_job.result()
    
    addresses = []
    total_rows = 0
    
    for row in results:
        total_rows += 1
        
        # Create standardized address
        std_address = standardize_address(
            row.addr_residential_street_number,
            row.addr_residential_street_name,
            row.city,
            row.state,
            row.zip_code
        )
        
        # Generate address_id
        address_id = generate_address_id(std_address)
        
        addresses.append({
            'address_id': address_id,
            'standardized_address': std_address,
            'street_number': row.addr_residential_street_number,
            'street_name': row.addr_residential_street_name,
            'city': row.city,
            'state': row.state,
            'zip_code': row.zip_code,
            'county': row.county,
            'latitude': row.latitude,
            'longitude': row.longitude,
            'geo_location': None,  # Will be created from lat/lng
            'geocoding_source': 'original_import',
            'geocoding_date': datetime.now().date(),
            'voter_count': row.voter_count
        })
        
        if total_rows % 1000 == 0:
            print(f"  Processed {total_rows:,} unique addresses...")
    
    print(f"\nExtracted {total_rows:,} unique geocoded addresses")
    
    # Get statistics
    counties = {}
    for addr in addresses:
        county = addr['county']
        if county not in counties:
            counties[county] = 0
        counties[county] += addr['voter_count']
    
    print("\nAddress distribution by county:")
    for county, count in sorted(counties.items()):
        print(f"  {county}: {count:,} voters")
    
    return addresses

def load_addresses_to_bigquery(client, addresses):
    """Load extracted addresses to the new addresses table."""
    
    print(f"\nLoading {len(addresses):,} addresses to BigQuery...")
    
    # Prepare data for loading
    rows_to_insert = []
    for addr in addresses:
        # Format geo_location for BigQuery
        if addr['latitude'] and addr['longitude']:
            geo_wkt = f"POINT({addr['longitude']} {addr['latitude']})"
        else:
            geo_wkt = None
        
        rows_to_insert.append({
            'address_id': addr['address_id'],
            'standardized_address': addr['standardized_address'],
            'street_number': addr['street_number'],
            'street_name': addr['street_name'],
            'street_suffix': None,  # Not in original data
            'city': addr['city'],
            'state': addr['state'],
            'zip_code': addr['zip_code'],
            'county': addr['county'],
            'geo_location': geo_wkt,
            'latitude': addr['latitude'],
            'longitude': addr['longitude'],
            'geocoding_source': addr['geocoding_source'],
            'geocoding_date': addr['geocoding_date'].isoformat(),
            'last_updated': datetime.now().isoformat()
        })
    
    # Load to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.addresses"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    job = client.load_table_from_json(
        rows_to_insert,
        table_id,
        job_config=job_config
    )
    
    job.result()
    print(f"Successfully loaded {len(addresses):,} addresses to {table_id}")
    
    return table_id

def verify_geocoding_preservation(client):
    """Verify that geocoding data was preserved correctly."""
    
    print("\nVerifying geocoding preservation...")
    
    # Check original voter geocoding count
    original_query = """
    SELECT COUNT(DISTINCT CONCAT(
        addr_residential_street_number, '|',
        addr_residential_street_name, '|',
        addr_residential_city, '|',
        addr_residential_zip_code
    )) as unique_geocoded
    FROM `proj-roth.voter_data.voters`
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    
    original_result = client.query(original_query).result()
    original_count = list(original_result)[0].unique_geocoded
    
    # Check new addresses table count
    new_query = """
    SELECT COUNT(*) as address_count
    FROM `proj-roth.voter_data.addresses`
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    
    new_result = client.query(new_query).result()
    new_count = list(new_result)[0].address_count
    
    print(f"  Original geocoded addresses: {original_count:,}")
    print(f"  Preserved geocoded addresses: {new_count:,}")
    
    if new_count >= original_count:
        print("  ✓ All geocoding data preserved successfully")
    else:
        print(f"  ⚠ Warning: {original_count - new_count} addresses may be missing")
    
    return new_count >= original_count

def main():
    """Main extraction process."""
    print(f"Starting geocoding extraction at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Extract geocoding data
    addresses = extract_geocoding_data(client)
    
    # Load to new addresses table
    table_id = load_addresses_to_bigquery(client, addresses)
    
    # Verify preservation
    success = verify_geocoding_preservation(client)
    
    if success:
        print("\nGeocoding extraction completed successfully!")
    else:
        print("\nGeocoding extraction completed with warnings")
    
    return addresses

if __name__ == "__main__":
    main()