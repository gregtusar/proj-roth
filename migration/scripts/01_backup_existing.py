#!/usr/bin/env python3
"""
Backup existing tables before migration.
Exports current voters and street_party_summary tables to GCS.
"""

import os
import sys
from datetime import datetime
from google.cloud import bigquery
from google.cloud import storage

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'
BACKUP_BUCKET = 'nj7voterfile'
BACKUP_PREFIX = f'backups/{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def backup_table_to_gcs(client, table_id, destination_uri):
    """Export a BigQuery table to GCS in Avro format."""
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    
    job_config = bigquery.ExtractJobConfig()
    job_config.destination_format = bigquery.DestinationFormat.AVRO
    job_config.use_avro_logical_types = True
    
    extract_job = client.extract_table(
        table_ref,
        destination_uri,
        job_config=job_config
    )
    
    print(f"Starting backup of {table_id} to {destination_uri}")
    extract_job.result()
    print(f"Backup of {table_id} completed")
    
    return destination_uri

def main():
    """Main backup process."""
    print(f"Starting backup process at {datetime.now()}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Backup location: gs://{BACKUP_BUCKET}/{BACKUP_PREFIX}")
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Tables to backup
    tables_to_backup = [
        'voters',
        'street_party_summary'
    ]
    
    backup_manifest = []
    
    for table_id in tables_to_backup:
        try:
            # Check if table exists
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
            table = bq_client.get_table(table_ref)
            
            print(f"\nBacking up {table_id}:")
            print(f"  Rows: {table.num_rows:,}")
            print(f"  Size: {table.num_bytes / (1024**3):.2f} GB")
            
            # Backup to GCS
            destination_uri = f"gs://{BACKUP_BUCKET}/{BACKUP_PREFIX}/{table_id}/*.avro"
            backup_location = backup_table_to_gcs(bq_client, table_id, destination_uri)
            
            backup_manifest.append({
                'table': table_id,
                'location': backup_location,
                'rows': table.num_rows,
                'bytes': table.num_bytes,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error backing up {table_id}: {e}")
            sys.exit(1)
    
    # Save backup manifest
    manifest_content = "Backup Manifest\n"
    manifest_content += f"Timestamp: {datetime.now()}\n"
    manifest_content += f"Project: {PROJECT_ID}\n"
    manifest_content += f"Dataset: {DATASET_ID}\n\n"
    
    for item in backup_manifest:
        manifest_content += f"\nTable: {item['table']}\n"
        manifest_content += f"  Location: {item['location']}\n"
        manifest_content += f"  Rows: {item['rows']:,}\n"
        manifest_content += f"  Size: {item['bytes'] / (1024**3):.2f} GB\n"
        manifest_content += f"  Timestamp: {item['timestamp']}\n"
    
    # Upload manifest to GCS
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BACKUP_BUCKET)
    blob = bucket.blob(f"{BACKUP_PREFIX}/manifest.txt")
    blob.upload_from_string(manifest_content)
    
    print(f"\nBackup manifest saved to gs://{BACKUP_BUCKET}/{BACKUP_PREFIX}/manifest.txt")
    print("\nBackup completed successfully!")
    
    return backup_manifest

if __name__ == "__main__":
    main()