#!/usr/bin/env python3
"""
Migration script to transfer data from BigQuery to PostgreSQL.
Handles data type conversions and maintains data integrity.
"""

import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from google.cloud import bigquery
import tempfile
from typing import Optional, Dict, Any
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigQueryToPostgresMigrator:
    """Migrates voter data from BigQuery to PostgreSQL."""
    
    def __init__(self, 
                 bq_project_id: str = 'proj-roth',
                 bq_dataset_id: str = 'voter_data',
                 pg_host: str = 'localhost',
                 pg_port: int = 5432,
                 pg_database: str = 'voter_data',
                 pg_user: str = 'postgres',
                 pg_password: str = None):
        
        self.bq_project_id = bq_project_id
        self.bq_dataset_id = bq_dataset_id
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_database = pg_database
        self.pg_user = pg_user
        self.pg_password = pg_password or os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        self.bq_client = None
        self.pg_conn = None
        self.creds_file_path = None
        
    def setup_bigquery_credentials(self):
        """Set up BigQuery credentials from environment variable."""
        credentials_json = os.getenv('GCP_CREDENTIALS')
        if not credentials_json:
            logger.error("GCP_CREDENTIALS environment variable not set")
            return False
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(credentials_json)
                self.creds_file_path = f.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_file_path
            self.bq_client = bigquery.Client(project=self.bq_project_id)
            logger.info("✅ BigQuery credentials configured")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up BigQuery credentials: {e}")
            return False
    
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password
            )
            self.pg_conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to PostgreSQL: {e}")
            return False
    
    def get_bigquery_voter_count(self) -> int:
        """Get total voter count from BigQuery."""
        query = f"SELECT COUNT(*) as count FROM `{self.bq_project_id}.{self.bq_dataset_id}.voters`"
        try:
            result = self.bq_client.query(query).to_dataframe()
            return int(result.iloc[0]['count'])
        except Exception as e:
            logger.error(f"Error getting BigQuery voter count: {e}")
            return 0
    
    def extract_voters_from_bigquery(self, batch_size: int = 10000, offset: int = 0) -> pd.DataFrame:
        """Extract voter data from BigQuery in batches with complete schema."""
        query = f"""
        SELECT 
            id,
            name_first,
            name_middle,
            name_last,
            demo_age,
            demo_race,
            demo_race_confidence,
            demo_gender,
            demo_party,
            addr_residential_street_name,
            addr_residential_street_number,
            addr_residential_line1,
            addr_residential_line2,
            addr_residential_line3,
            addr_residential_city,
            addr_residential_state,
            addr_residential_zip_code,
            county_name,
            congressional_name,
            state_house_name,
            state_senate_name,
            precinct_name,
            municipal_name,
            place_name,
            city_council_name,
            email,
            phone_1,
            phone_2,
            registration_status_civitech,
            voter_type,
            current_voter_registration_intent,
            current_support_score,
            current_tags,
            score_support_generic_dem,
            participation_primary_2016,
            participation_primary_2017,
            participation_primary_2018,
            participation_primary_2019,
            participation_primary_2020,
            participation_primary_2021,
            participation_primary_2022,
            participation_primary_2023,
            participation_primary_2024,
            participation_general_2016,
            participation_general_2017,
            participation_general_2018,
            participation_general_2019,
            participation_general_2020,
            participation_general_2021,
            participation_general_2022,
            participation_general_2023,
            participation_general_2024,
            vote_primary_dem_2016,
            vote_primary_rep_2016,
            vote_primary_dem_2017,
            vote_primary_rep_2017,
            vote_primary_dem_2018,
            vote_primary_rep_2018,
            vote_primary_dem_2019,
            vote_primary_rep_2019,
            vote_primary_dem_2020,
            vote_primary_rep_2020,
            vote_primary_dem_2021,
            vote_primary_rep_2021,
            vote_primary_dem_2022,
            vote_primary_rep_2022,
            vote_primary_dem_2023,
            vote_primary_rep_2023,
            vote_primary_dem_2024,
            vote_primary_rep_2024,
            vote_other_2016,
            vote_other_2017,
            vote_other_2018,
            vote_other_2019,
            vote_other_2020,
            vote_other_2021,
            vote_other_2022,
            vote_other_2023,
            vote_other_2024,
            notes,
            ST_X(location) as longitude,
            ST_Y(location) as latitude,
            geocoding_accuracy,
            geocoding_source,
            geocoding_date,
            geocoding_confidence,
            standardized_address,
            census_block_fips,
            census_tract_fips,
            created_at,
            updated_at
        FROM `{self.bq_project_id}.{self.bq_dataset_id}.voters`
        ORDER BY id
        LIMIT {batch_size}
        OFFSET {offset}
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            logger.info(f"Extracted {len(df)} voters from BigQuery (offset: {offset})")
            return df
        except Exception as e:
            logger.error(f"Error extracting voters from BigQuery: {e}")
            return pd.DataFrame()
    
    def clean_data_for_postgres(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types for PostgreSQL compatibility."""
        df_clean = df.copy()
        
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        
        if 'demo_birth_date' in df_clean.columns:
            df_clean['demo_birth_date'] = pd.to_datetime(df_clean['demo_birth_date'], errors='coerce')
        
        if 'geocoding_timestamp' in df_clean.columns:
            df_clean['geocoding_timestamp'] = pd.to_datetime(df_clean['geocoding_timestamp'], errors='coerce')
        
        if 'demo_age' in df_clean.columns:
            df_clean['demo_age'] = pd.to_numeric(df_clean['demo_age'], errors='coerce')
        
        if 'latitude' in df_clean.columns:
            df_clean['latitude'] = pd.to_numeric(df_clean['latitude'], errors='coerce')
        
        if 'longitude' in df_clean.columns:
            df_clean['longitude'] = pd.to_numeric(df_clean['longitude'], errors='coerce')
        
        string_columns = df_clean.select_dtypes(include=['object']).columns
        for col in string_columns:
            if col not in ['demo_birth_date', 'geocoding_timestamp']:
                df_clean[col] = df_clean[col].astype(str).str[:255]
                df_clean[col] = df_clean[col].replace('nan', None)
        
        logger.info(f"Cleaned {len(df_clean)} voter records for PostgreSQL")
        return df_clean
    
    def insert_voters_to_postgres(self, df: pd.DataFrame):
        """Insert voter data into PostgreSQL using batch insert."""
        if df.empty:
            return
        
        columns = list(df.columns)
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        
        data_tuples = [tuple(row) for row in df.to_numpy()]
        
        insert_query = f"""
        INSERT INTO voters ({column_names})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])},
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.pg_conn.cursor() as cursor:
                execute_values(
                    cursor,
                    insert_query,
                    data_tuples,
                    template=None,
                    page_size=1000
                )
            logger.info(f"✅ Inserted {len(df)} voters into PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Error inserting voters into PostgreSQL: {e}")
            raise
    
    def migrate_voters(self, batch_size: int = 10000):
        """Migrate all voter data from BigQuery to PostgreSQL."""
        logger.info("🚀 Starting voter data migration...")
        
        total_voters = self.get_bigquery_voter_count()
        logger.info(f"📊 Total voters to migrate: {total_voters:,}")
        
        if total_voters == 0:
            logger.warning("No voters found in BigQuery")
            return False
        
        migrated_count = 0
        offset = 0
        
        while offset < total_voters:
            logger.info(f"📦 Processing batch {offset//batch_size + 1} (offset: {offset:,})")
            
            df = self.extract_voters_from_bigquery(batch_size, offset)
            
            if df.empty:
                break
            
            df_clean = self.clean_data_for_postgres(df)
            
            self.insert_voters_to_postgres(df_clean)
            
            migrated_count += len(df)
            offset += batch_size
            
            progress_pct = (migrated_count / total_voters) * 100
            logger.info(f"📈 Progress: {migrated_count:,}/{total_voters:,} ({progress_pct:.1f}%)")
        
        logger.info(f"✅ Migration completed! Migrated {migrated_count:,} voters")
        return True
    
    def verify_migration(self):
        """Verify migration by comparing record counts."""
        logger.info("🔍 Verifying migration...")
        
        bq_count = self.get_bigquery_voter_count()
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM voters")
                pg_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting PostgreSQL count: {e}")
            return False
        
        logger.info(f"📊 BigQuery voters: {bq_count:,}")
        logger.info(f"📊 PostgreSQL voters: {pg_count:,}")
        
        if bq_count == pg_count:
            logger.info("✅ Migration verification successful!")
            return True
        else:
            logger.error(f"❌ Migration verification failed! Missing {bq_count - pg_count} records")
            return False
    
    def cleanup(self):
        """Clean up connections and temporary files."""
        if self.pg_conn:
            self.pg_conn.close()
        
        if self.creds_file_path and os.path.exists(self.creds_file_path):
            try:
                os.unlink(self.creds_file_path)
            except:
                pass

def main():
    """Main migration execution."""
    logger.info("🔄 BigQuery to PostgreSQL Migration Tool")
    logger.info("=" * 50)
    
    pg_config = {
        'pg_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'pg_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'pg_database': os.getenv('POSTGRES_DATABASE', 'voter_data'),
        'pg_user': os.getenv('POSTGRES_USER', 'postgres'),
        'pg_password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    migrator = BigQueryToPostgresMigrator(**pg_config)
    
    try:
        if not migrator.setup_bigquery_credentials():
            logger.error("Failed to setup BigQuery credentials")
            return False
        
        if not migrator.connect_postgres():
            logger.error("Failed to connect to PostgreSQL")
            return False
        
        if not migrator.migrate_voters():
            logger.error("Migration failed")
            return False
        
        if not migrator.verify_migration():
            logger.error("Migration verification failed")
            return False
        
        logger.info("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        return False
    finally:
        migrator.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
