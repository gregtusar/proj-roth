#!/usr/bin/env python3
"""
Setup script for BigQuery voter data analysis environment.
This script initializes the BigQuery dataset, tables, and imports the voter data.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigQuerySetup:
    """Setup BigQuery environment for voter data analysis."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data'):
        """Initialize the setup class."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = None
        
    def setup_credentials(self, credentials_json: str):
        """Set up BigQuery client with provided credentials."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(credentials_json)
            creds_file_path = f.name
        
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file_path
            self.bq_client = bigquery.Client(project=self.project_id)
            logger.info(f"✅ Successfully initialized BigQuery client for project: {self.project_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up credentials: {e}")
            return False
        finally:
            try:
                os.unlink(creds_file_path)
            except:
                pass
    
    def create_dataset(self):
        """Create the voter_data dataset if it doesn't exist."""
        if not self.bq_client:
            logger.error("BigQuery client not initialized")
            return False
        
        dataset_ref = self.bq_client.dataset(self.dataset_id)
        
        try:
            self.bq_client.get_dataset(dataset_ref)
            logger.info(f"✅ Dataset {self.dataset_id} already exists")
            return True
        except NotFound:
            try:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                dataset.description = "New Jersey voter registration data with geolocation for political mapping"
                
                dataset = self.bq_client.create_dataset(dataset)
                logger.info(f"✅ Created dataset {self.dataset_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Error creating dataset: {e}")
                return False
    
    def create_tables(self):
        """Create the required tables with proper schema."""
        if not self.bq_client:
            logger.error("BigQuery client not initialized")
            return False
        
        schema_file = Path(__file__).parent / "bigquery_schema.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            statements = []
            current_statement = ""
            in_create_table = False
            
            for line in schema_sql.split('\n'):
                line = line.strip()
                
                if line.startswith('--') or line.startswith('/*') or not line:
                    continue
                
                if line.upper().startswith('CREATE OR REPLACE TABLE'):
                    in_create_table = True
                    current_statement = line
                elif in_create_table:
                    current_statement += " " + line
                    if line.endswith(';'):
                        statements.append(current_statement.rstrip(';'))
                        current_statement = ""
                        in_create_table = False
            
            for statement in statements:
                if 'CREATE OR REPLACE TABLE' in statement:
                    try:
                        query_job = self.bq_client.query(statement)
                        query_job.result()
                        
                        table_name = statement.split('`')[1].split('.')[-1]
                        logger.info(f"✅ Created table: {table_name}")
                    except Exception as e:
                        logger.error(f"❌ Error creating table: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error reading schema file: {e}")
            return False
    
    def import_voter_data(self, csv_path: str):
        """Import voter data from CSV file to BigQuery."""
        if not self.bq_client:
            logger.error("BigQuery client not initialized")
            return False
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        try:
            logger.info(f"📊 Loading voter data from {csv_path}")
            
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"✅ Loaded {len(df)} voter records")
            
            df = self.clean_voter_data(df)
            
            table_id = f"{self.project_id}.{self.dataset_id}.voters"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Replace existing data
                autodetect=False,  # Use explicit schema
                allow_quoted_newlines=True,
                allow_jagged_rows=True,
                ignore_unknown_values=True
            )
            
            logger.info(f"⬆️  Importing data to BigQuery table: {table_id}")
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            table = self.bq_client.get_table(table_id)
            logger.info(f"✅ Successfully imported {table.num_rows} rows to BigQuery")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing voter data: {e}")
            return False
    
    def clean_voter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare voter data for BigQuery import."""
        logger.info("🧹 Cleaning voter data...")
        
        boolean_columns = [col for col in df.columns if 'participation_' in col or 'vote_primary_' in col]
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        numeric_columns = ['demo_age', 'addr_residential_zip_code', 'phone_1', 'phone_2']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        float_columns = ['current_voter_registration_intent', 'current_support_score', 'score_support_generic_dem']
        for col in float_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.where(pd.notnull(df), None)
        
        logger.info(f"✅ Data cleaning completed. Shape: {df.shape}")
        return df
    
    def verify_setup(self):
        """Verify that the BigQuery setup is working correctly."""
        if not self.bq_client:
            logger.error("BigQuery client not initialized")
            return False
        
        try:
            dataset_ref = self.bq_client.dataset(self.dataset_id)
            dataset = self.bq_client.get_dataset(dataset_ref)
            logger.info(f"✅ Dataset verified: {dataset.dataset_id}")
            
            tables_to_check = ['voters']
            
            for table_name in tables_to_check:
                table_ref = dataset.table(table_name)
                table = self.bq_client.get_table(table_ref)
                logger.info(f"✅ Table verified: {table_name} ({table.num_rows} rows)")
            
            test_query = f"""
            SELECT 
                COUNT(*) as total_voters,
                COUNT(DISTINCT demo_party) as unique_parties,
                COUNT(DISTINCT county_name) as unique_counties
            FROM `{self.project_id}.{self.dataset_id}.voters`
            """
            
            result = self.bq_client.query(test_query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                logger.info(f"✅ Test query successful:")
                logger.info(f"   Total voters: {row['total_voters']}")
                logger.info(f"   Unique parties: {row['unique_parties']}")
                logger.info(f"   Unique counties: {row['unique_counties']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

def main():
    """Main setup function."""
    print("🗳️  BIGQUERY VOTER DATA SETUP")
    print("=" * 50)
    
    setup = BigQuerySetup()
    
    credentials_json = os.getenv('GCP_CREDENTIALS')
    
    if not credentials_json:
        print("Please provide GCP service account credentials.")
        print("You can either:")
        print("1. Set the GCP_CREDENTIALS environment variable")
        print("2. Provide the path to your service account JSON file")
        print("\nExample:")
        print("export GCP_CREDENTIALS='$(cat /path/to/service-account.json)'")
        print("python setup_bigquery_environment.py")
        logger.error("❌ No GCP credentials provided")
        return False
    
    if not setup.setup_credentials(credentials_json):
        logger.error("Failed to setup credentials")
        return False
    
    if not setup.create_dataset():
        logger.error("Failed to create dataset")
        return False
    
    if not setup.create_tables():
        logger.error("Failed to create tables")
        return False
    
    csv_path = "/home/ubuntu/export-20250729.csv"
    if os.path.exists(csv_path):
        if not setup.import_voter_data(csv_path):
            logger.error("Failed to import voter data")
            return False
    else:
        logger.warning(f"Voter data file not found: {csv_path}")
        logger.info("You can import data later using the BigQueryVoterGeocodingPipeline")
    
    if not setup.verify_setup():
        logger.error("Setup verification failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 BIGQUERY SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"✅ Dataset: {setup.project_id}.{setup.dataset_id}")
    print("✅ Tables: voters, street_party_summary")
    print("✅ Data imported and verified")
    print("\nNext steps:")
    print("1. Run geocoding pipeline to add location data")
    print("2. Generate street-level party summary")
    print("3. Create mapping visualizations")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
