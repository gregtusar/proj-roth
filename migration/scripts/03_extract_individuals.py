#!/usr/bin/env python3
"""
Extract unique individuals from voters table using entity resolution.
Creates master records for unique people based on name and address matching.
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime
from google.cloud import bigquery

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.fuzzy_matcher import normalize_name, create_standardized_name

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'

def generate_master_id(standardized_name, address_id=None):
    """Generate a deterministic master_id for an individual."""
    # Use name and address for unique ID
    unique_string = f"{standardized_name}|{address_id or 'NO_ADDR'}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def extract_unique_individuals(client):
    """Extract unique individuals from voters table."""
    
    print("Extracting unique individuals from voters table...")
    
    # Query to get all unique name/address combinations
    query = """
    SELECT DISTINCT
        name_first,
        name_middle,
        name_last,
        addr_residential_street_number,
        addr_residential_street_name,
        addr_residential_city,
        addr_residential_state,
        addr_residential_zip_code,
        COUNT(*) as voter_count
    FROM `proj-roth.voter_data.voters`
    WHERE name_last IS NOT NULL
    GROUP BY 1,2,3,4,5,6,7,8
    ORDER BY name_last, name_first
    """
    
    print("Running extraction query...")
    query_job = client.query(query)
    results = query_job.result()
    
    # Process results and create unique individuals
    individuals = {}  # key: standardized_name -> individual record
    address_lookup = {}  # for matching addresses to address_ids
    
    # First, build address lookup from addresses table
    print("Building address lookup...")
    addr_query = """
    SELECT 
        address_id,
        standardized_address,
        street_number,
        street_name,
        city,
        state,
        zip_code
    FROM `proj-roth.voter_data.addresses`
    """
    
    addr_results = client.query(addr_query).result()
    for row in addr_results:
        # Create lookup key
        addr_key = f"{row.street_number or ''}|{row.street_name or ''}|{row.city or ''}|{row.zip_code or ''}"
        address_lookup[addr_key.upper()] = row.address_id
    
    print(f"Loaded {len(address_lookup):,} addresses for matching")
    
    # Process voters to extract individuals
    total_rows = 0
    duplicate_count = 0
    
    for row in results:
        total_rows += 1
        
        # Create standardized name
        std_name = create_standardized_name(
            row.name_first,
            row.name_middle,
            row.name_last
        )
        
        # Find matching address_id
        addr_key = f"{row.addr_residential_street_number or ''}|{row.addr_residential_street_name or ''}|{row.addr_residential_city or ''}|{row.addr_residential_zip_code or ''}"
        address_id = address_lookup.get(addr_key.upper())
        
        # Create individual key for deduplication
        individual_key = f"{std_name}|{address_id or 'NO_ADDR'}"
        
        if individual_key not in individuals:
            # New unique individual
            master_id = generate_master_id(std_name, address_id)
            
            individuals[individual_key] = {
                'master_id': master_id,
                'standardized_name': std_name,
                'name_first': normalize_name(row.name_first) if row.name_first else None,
                'name_middle': normalize_name(row.name_middle) if row.name_middle else None,
                'name_last': normalize_name(row.name_last) if row.name_last else None,
                'name_suffix': None,  # Not in current data
                'address_id': address_id,
                'voter_count': row.voter_count
            }
        else:
            # Duplicate - aggregate voter count
            individuals[individual_key]['voter_count'] += row.voter_count
            duplicate_count += 1
        
        if total_rows % 10000 == 0:
            print(f"  Processed {total_rows:,} name/address combinations...")
    
    print(f"\nProcessed {total_rows:,} total combinations")
    print(f"Found {len(individuals):,} unique individuals")
    print(f"Merged {duplicate_count:,} duplicate records")
    
    return list(individuals.values())

def load_individuals_to_bigquery(client, individuals):
    """Load extracted individuals to BigQuery."""
    
    print(f"\nLoading {len(individuals):,} individuals to BigQuery...")
    
    # Prepare data for loading
    rows_to_insert = []
    for ind in individuals:
        rows_to_insert.append({
            'master_id': ind['master_id'],
            'standardized_name': ind['standardized_name'],
            'name_first': ind['name_first'],
            'name_middle': ind['name_middle'],
            'name_last': ind['name_last'],
            'name_suffix': ind['name_suffix'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
    
    # Load to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.individuals"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    job = client.load_table_from_json(
        rows_to_insert,
        table_id,
        job_config=job_config
    )
    
    job.result()
    print(f"Successfully loaded {len(individuals):,} individuals to {table_id}")
    
    return len(individuals)

def create_individual_address_links(client, individuals):
    """Create links between individuals and addresses."""
    
    print("\nCreating individual-address links...")
    
    # Filter individuals with addresses
    individuals_with_addr = [ind for ind in individuals if ind.get('address_id')]
    
    print(f"Linking {len(individuals_with_addr):,} individuals to addresses...")
    
    rows_to_insert = []
    for ind in individuals_with_addr:
        link_id = str(uuid.uuid4())
        
        rows_to_insert.append({
            'individual_address_id': link_id,
            'master_id': ind['master_id'],
            'address_id': ind['address_id'],
            'address_type': 'residential',
            'valid_from': datetime.now().date().isoformat(),
            'valid_to': None,
            'is_current': True,
            'source_system': 'voter_file',
            'created_at': datetime.now().isoformat()
        })
    
    # Load to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.individual_addresses"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    job = client.load_table_from_json(
        rows_to_insert,
        table_id,
        job_config=job_config
    )
    
    job.result()
    print(f"Successfully created {len(rows_to_insert):,} individual-address links")
    
    return len(rows_to_insert)

def verify_individual_extraction(client):
    """Verify that individuals were extracted correctly."""
    
    print("\nVerifying individual extraction...")
    
    # Check original voter count
    original_query = """
    SELECT COUNT(DISTINCT CONCAT(
        COALESCE(name_first, ''), '|',
        COALESCE(name_middle, ''), '|',
        COALESCE(name_last, ''), '|',
        COALESCE(CAST(addr_residential_street_number AS STRING), ''), '|',
        COALESCE(addr_residential_street_name, ''), '|',
        COALESCE(addr_residential_zip_code, '')
    )) as unique_individuals
    FROM `proj-roth.voter_data.voters`
    WHERE name_last IS NOT NULL
    """
    
    original_result = client.query(original_query).result()
    original_count = list(original_result)[0].unique_individuals
    
    # Check new individuals table count
    new_query = """
    SELECT COUNT(*) as individual_count
    FROM `proj-roth.voter_data.individuals`
    """
    
    new_result = client.query(new_query).result()
    new_count = list(new_result)[0].individual_count
    
    print(f"  Original unique name/address combinations: {original_count:,}")
    print(f"  Extracted individuals: {new_count:,}")
    
    # Check address links
    link_query = """
    SELECT COUNT(*) as link_count
    FROM `proj-roth.voter_data.individual_addresses`
    """
    
    link_result = client.query(link_query).result()
    link_count = list(link_result)[0].link_count
    
    print(f"  Individual-address links created: {link_count:,}")
    
    return True

def main():
    """Main extraction process."""
    print(f"Starting individual extraction at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Extract unique individuals
    individuals = extract_unique_individuals(client)
    
    # Load to individuals table
    individual_count = load_individuals_to_bigquery(client, individuals)
    
    # Create individual-address links
    link_count = create_individual_address_links(client, individuals)
    
    # Verify extraction
    verify_individual_extraction(client)
    
    print(f"\nIndividual extraction completed successfully!")
    print(f"  Individuals: {individual_count:,}")
    print(f"  Address links: {link_count:,}")
    
    return individuals

if __name__ == "__main__":
    main()