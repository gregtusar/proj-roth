#!/usr/bin/env python3
"""
Load raw CSV data into BigQuery raw tables.
Handles data type conversions and validation.
"""

import os
import sys
from datetime import datetime
import uuid
from google.cloud import bigquery
from google.cloud import storage

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'
BUCKET_NAME = 'nj7voterfile'

# Source files in GCS
VOTER_FILE = 'secondvoterfile.csv'  # Latest voter file (August 2024)
DONATION_FILE = 'donations.csv'

def load_voters_from_gcs(client):
    """Load voter CSV from GCS into raw_voters table."""
    
    print(f"\nLoading voters from gs://{BUCKET_NAME}/{VOTER_FILE}")
    
    # Configure the load job
    table_id = f"{PROJECT_ID}.{DATASET_ID}.raw_voters"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # Skip header row
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        # Define schema with proper types
        schema=[
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("addr_residential_street_name", "STRING"),
            bigquery.SchemaField("addr_residential_street_number", "STRING"),
            bigquery.SchemaField("name_first", "STRING"),
            bigquery.SchemaField("name_middle", "STRING"),
            bigquery.SchemaField("name_last", "STRING"),
            bigquery.SchemaField("demo_age", "INT64"),
            bigquery.SchemaField("demo_race", "STRING"),
            bigquery.SchemaField("demo_race_confidence", "STRING"),
            bigquery.SchemaField("demo_gender", "STRING"),
            bigquery.SchemaField("addr_residential_state", "STRING"),
            bigquery.SchemaField("addr_residential_city", "STRING"),
            bigquery.SchemaField("current_voter_registration_intent", "STRING"),
            bigquery.SchemaField("current_support_score", "FLOAT64"),
            bigquery.SchemaField("current_tags", "STRING"),
            bigquery.SchemaField("score_support_generic_dem", "FLOAT64"),
            bigquery.SchemaField("demo_party", "STRING"),
            bigquery.SchemaField("registration_status_civitech", "STRING"),
            bigquery.SchemaField("addr_residential_line1", "STRING"),
            bigquery.SchemaField("addr_residential_line2", "STRING"),
            bigquery.SchemaField("addr_residential_line3", "STRING"),
            bigquery.SchemaField("addr_residential_zip_code", "STRING"),
            bigquery.SchemaField("county_name", "STRING"),
            bigquery.SchemaField("email", "STRING"),
            bigquery.SchemaField("phone_1", "STRING"),
            bigquery.SchemaField("phone_2", "STRING"),
            bigquery.SchemaField("congressional_name", "STRING"),
            bigquery.SchemaField("state_house_name", "STRING"),
            bigquery.SchemaField("state_senate_name", "STRING"),
            bigquery.SchemaField("precinct_name", "STRING"),
            bigquery.SchemaField("municipal_name", "STRING"),
            bigquery.SchemaField("place_name", "STRING"),
            bigquery.SchemaField("city_council_name", "STRING"),
            bigquery.SchemaField("voter_type", "STRING"),
            # Participation columns - CSV has TRUE/FALSE strings
            bigquery.SchemaField("participation_primary_2016", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2017", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2018", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2019", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2020", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2021", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2022", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2023", "BOOLEAN"),
            bigquery.SchemaField("participation_primary_2024", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2016", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2017", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2018", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2019", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2020", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2021", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2022", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2023", "BOOLEAN"),
            bigquery.SchemaField("participation_general_2024", "BOOLEAN"),
            # Vote columns
            bigquery.SchemaField("vote_primary_dem_2016", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2016", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2017", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2017", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2018", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2018", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2019", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2019", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2020", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2020", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2021", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2021", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2022", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2022", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2023", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2023", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_dem_2024", "BOOLEAN"),
            bigquery.SchemaField("vote_primary_rep_2024", "BOOLEAN"),
            # Other vote columns (vote method: IN PERSON, MAIL, etc.)
            bigquery.SchemaField("vote_other_2016", "STRING"),
            bigquery.SchemaField("vote_other_2017", "STRING"),
            bigquery.SchemaField("vote_other_2018", "STRING"),
            bigquery.SchemaField("vote_other_2019", "STRING"),
            bigquery.SchemaField("vote_other_2020", "STRING"),
            bigquery.SchemaField("vote_other_2021", "STRING"),
            bigquery.SchemaField("vote_other_2022", "STRING"),
            bigquery.SchemaField("vote_other_2023", "STRING"),
            bigquery.SchemaField("vote_other_2024", "STRING"),
            bigquery.SchemaField("notes", "STRING"),
        ],
        # Add import metadata fields
        field_delimiter=",",
        allow_quoted_newlines=True,
        allow_jagged_rows=False,
    )
    
    # Generate batch ID
    batch_id = str(uuid.uuid4())[:8]
    
    # Load from GCS
    uri = f"gs://{BUCKET_NAME}/{VOTER_FILE}"
    
    load_job = client.load_table_from_uri(
        uri,
        table_id,
        job_config=job_config
    )
    
    print(f"  Loading with batch_id: {batch_id}")
    print("  Waiting for job to complete...")
    
    load_job.result()  # Wait for job to complete
    
    # Note: batch_id and timestamp are handled by table defaults
    
    # Get statistics
    table = client.get_table(table_id)
    print(f"  ✓ Loaded {table.num_rows:,} voter records")
    
    return table.num_rows

def load_donations_from_gcs(client):
    """Load donation CSV from GCS into raw_donations table."""
    
    print(f"\nLoading donations from gs://{BUCKET_NAME}/{DONATION_FILE}")
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.raw_donations"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("committee_name", "STRING"),
            bigquery.SchemaField("full_name", "STRING"),
            bigquery.SchemaField("first_name", "STRING"),
            bigquery.SchemaField("middle_name", "STRING"),
            bigquery.SchemaField("last_name", "STRING"),
            bigquery.SchemaField("suffix", "STRING"),
            bigquery.SchemaField("address_1", "STRING"),
            bigquery.SchemaField("address_2", "STRING"),
            bigquery.SchemaField("city", "STRING"),
            bigquery.SchemaField("state", "STRING"),
            bigquery.SchemaField("zip", "STRING"),
            bigquery.SchemaField("employer", "STRING"),
            bigquery.SchemaField("occupation", "STRING"),
            bigquery.SchemaField("contribution_amount", "NUMERIC"),
            bigquery.SchemaField("election_type", "STRING"),
            bigquery.SchemaField("election_year", "INT64"),
        ],
        field_delimiter=",",
        allow_quoted_newlines=True,
    )
    
    # Generate batch ID
    batch_id = str(uuid.uuid4())[:8]
    
    # Load from GCS
    uri = f"gs://{BUCKET_NAME}/{DONATION_FILE}"
    
    load_job = client.load_table_from_uri(
        uri,
        table_id,
        job_config=job_config
    )
    
    print(f"  Loading with batch_id: {batch_id}")
    print("  Waiting for job to complete...")
    
    load_job.result()
    
    # Note: batch_id and timestamp are handled by table defaults
    
    # Get statistics
    table = client.get_table(table_id)
    print(f"  ✓ Loaded {table.num_rows:,} donation records")
    
    return table.num_rows

def validate_data_quality(client):
    """Run basic data quality checks on loaded data."""
    
    print("\nValidating data quality...")
    
    # Check for required fields in voters
    voter_check = """
    SELECT 
        COUNTIF(id IS NULL) as null_ids,
        COUNTIF(name_last IS NULL) as null_last_names,
        COUNTIF(county_name IS NULL) as null_counties,
        COUNT(*) as total_records
    FROM `proj-roth.voter_data.raw_voters`
    """
    
    results = client.query(voter_check).result()
    for row in results:
        print(f"  Voter data:")
        print(f"    Total records: {row.total_records:,}")
        print(f"    Null IDs: {row.null_ids:,}")
        print(f"    Null last names: {row.null_last_names:,}")
        print(f"    Null counties: {row.null_counties:,}")
    
    # Check boolean conversion
    bool_check = """
    SELECT 
        COUNTIF(participation_general_2020 IS TRUE) as voted_2020,
        COUNTIF(participation_general_2020 IS FALSE) as not_voted_2020,
        COUNTIF(participation_general_2020 IS NULL) as null_2020,
        COUNT(*) as total
    FROM `proj-roth.voter_data.raw_voters`
    """
    
    results = client.query(bool_check).result()
    for row in results:
        print(f"  Boolean conversion (2020 general):")
        print(f"    Voted: {row.voted_2020:,}")
        print(f"    Did not vote: {row.not_voted_2020:,}")
        print(f"    Null: {row.null_2020:,}")
    
    # Check donations
    donation_check = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT CONCAT(first_name, ' ', last_name)) as unique_donors,
        SUM(contribution_amount) as total_contributions
    FROM `proj-roth.voter_data.raw_donations`
    """
    
    results = client.query(donation_check).result()
    for row in results:
        print(f"  Donation data:")
        print(f"    Total records: {row.total_records:,}")
        print(f"    Unique donors: {row.unique_donors:,}")
        print(f"    Total contributions: ${row.total_contributions:,.2f}")

def main():
    """Main loading process."""
    print(f"Starting raw data load at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Source bucket: {BUCKET_NAME}")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    try:
        # Load voter data
        voter_count = load_voters_from_gcs(client)
        
        # Load donation data
        donation_count = load_donations_from_gcs(client)
        
        # Validate data quality
        validate_data_quality(client)
        
        print(f"\n✓ Raw data load completed successfully!")
        print(f"  Voters: {voter_count:,}")
        print(f"  Donations: {donation_count:,}")
        
    except Exception as e:
        print(f"\n✗ Error during data load: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()