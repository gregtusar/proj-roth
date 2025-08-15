#!/usr/bin/env python3
"""
Script to add geocoding columns to the existing BigQuery voters table.
"""

import os
import tempfile
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_credentials():
    """Set up GCP credentials from environment variable."""
    credentials_json = os.getenv('GCP_CREDENTIALS')
    if not credentials_json:
        logger.error("No GCP_CREDENTIALS found")
        return None, None
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(credentials_json)
            creds_file_path = f.name
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file_path
        client = bigquery.Client(project='proj-roth')
        logger.info("✅ Successfully set up GCP credentials")
        return client, creds_file_path
    except Exception as e:
        logger.error(f"❌ Error setting up credentials: {e}")
        return None, None

def add_geocoding_columns():
    """Add geocoding columns to the voters table."""
    client, creds_file = setup_credentials()
    if not client:
        return False
    
    try:
        table_id = "proj-roth.voter_data.voters"
        
        new_columns = [
            bigquery.SchemaField("latitude", "FLOAT64", mode="NULLABLE", description="Latitude coordinate from geocoding"),
            bigquery.SchemaField("longitude", "FLOAT64", mode="NULLABLE", description="Longitude coordinate from geocoding"),
            bigquery.SchemaField("geocoding_accuracy", "STRING", mode="NULLABLE", description="Accuracy level of geocoding result"),
            bigquery.SchemaField("geocoding_source", "STRING", mode="NULLABLE", description="Source of geocoding (Google Maps, Census, etc.)"),
            bigquery.SchemaField("geocoding_timestamp", "TIMESTAMP", mode="NULLABLE", description="When geocoding was performed"),
            bigquery.SchemaField("full_address", "STRING", mode="NULLABLE", description="Complete formatted address for geocoding")
        ]
        
        table = client.get_table(table_id)
        logger.info(f"Current table has {len(table.schema)} columns")
        
        existing_columns = {field.name for field in table.schema}
        columns_to_add = [col for col in new_columns if col.name not in existing_columns]
        
        if not columns_to_add:
            logger.info("All geocoding columns already exist")
            return True
        
        new_schema = list(table.schema) + columns_to_add
        table.schema = new_schema
        
        table = client.update_table(table, ["schema"])
        logger.info(f"✅ Added {len(columns_to_add)} geocoding columns to table")
        
        for col in columns_to_add:
            logger.info(f"  Added: {col.name} ({col.field_type})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding geocoding columns: {e}")
        return False
    finally:
        if creds_file and os.path.exists(creds_file):
            try:
                os.unlink(creds_file)
            except:
                pass

if __name__ == "__main__":
    success = add_geocoding_columns()
    if success:
        print("✅ Geocoding columns added successfully!")
    else:
        print("❌ Failed to add geocoding columns")
