#!/usr/bin/env python3
"""
Standalone script to refresh the street_party_summary table in BigQuery.

This script creates/updates the street-level party summary table by aggregating
geocoded voter data from the main voters table.
"""

import os
import logging
import tempfile
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StreetSummaryRefresher:
    """Handles refreshing the street_party_summary table."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data'):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.creds_file_path = None
        
        self._setup_credentials()
        self.bq_client = bigquery.Client(project=project_id)
        
    def refresh_street_summary(self):
        """Refresh the street-level party summary table."""
        logger.info("Starting street_party_summary table refresh...")
        
        query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset_id}.street_party_summary` AS
        SELECT 
            addr_residential_street_name as street_name,
            addr_residential_city as city,
            county_name as county,
            addr_residential_zip_code as zip_code,
            
            COUNTIF(demo_party = 'REPUBLICAN') as republican_count,
            COUNTIF(demo_party = 'DEMOCRAT') as democrat_count,
            COUNTIF(demo_party = 'UNAFFILIATED') as unaffiliated_count,
            COUNTIF(demo_party NOT IN ('REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED')) as other_party_count,
            COUNT(*) as total_voters,
            
            ROUND(COUNTIF(demo_party = 'REPUBLICAN') * 100.0 / COUNT(*), 2) as republican_pct,
            ROUND(COUNTIF(demo_party = 'DEMOCRAT') * 100.0 / COUNT(*), 2) as democrat_pct,
            ROUND(COUNTIF(demo_party = 'UNAFFILIATED') * 100.0 / COUNT(*), 2) as unaffiliated_pct,
            
            AVG(latitude) as street_center_latitude,
            AVG(longitude) as street_center_longitude,
            
            CURRENT_TIMESTAMP() as last_updated
            
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE addr_residential_street_name IS NOT NULL 
          AND latitude IS NOT NULL 
          AND longitude IS NOT NULL
        GROUP BY addr_residential_street_name, addr_residential_city, county_name, addr_residential_zip_code
        HAVING COUNT(*) >= 3
        """
        
        try:
            logger.info("Executing street summary refresh query...")
            query_job = self.bq_client.query(query)
            query_job.result()  # Wait for completion
            
            logger.info("Street party summary table refreshed successfully!")
            
            self.get_summary_stats()
            
        except Exception as e:
            logger.error(f"Error refreshing street summary: {e}")
            raise
    
    def get_summary_stats(self):
        """Get statistics about the refreshed street_party_summary table."""
        stats_query = f"""
        SELECT 
            COUNT(*) as total_streets,
            SUM(total_voters) as total_voters_in_summary,
            AVG(total_voters) as avg_voters_per_street,
            MIN(total_voters) as min_voters_per_street,
            MAX(total_voters) as max_voters_per_street,
            COUNT(DISTINCT county) as counties_represented,
            COUNT(DISTINCT city) as cities_represented
        FROM `{self.project_id}.{self.dataset_id}.street_party_summary`
        """
        
        try:
            result = self.bq_client.query(stats_query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                logger.info("=== Street Summary Statistics ===")
                logger.info(f"Total streets: {int(row['total_streets']):,}")
                logger.info(f"Total voters in summary: {int(row['total_voters_in_summary']):,}")
                logger.info(f"Average voters per street: {row['avg_voters_per_street']:.1f}")
                logger.info(f"Min voters per street: {int(row['min_voters_per_street'])}")
                logger.info(f"Max voters per street: {int(row['max_voters_per_street'])}")
                logger.info(f"Counties represented: {int(row['counties_represented'])}")
                logger.info(f"Cities represented: {int(row['cities_represented'])}")
                logger.info("=== End Statistics ===")
        except Exception as e:
            logger.warning(f"Could not retrieve summary statistics: {e}")
    
    def _setup_credentials(self):
        """Set up GCP credentials from environment variable."""
        credentials_json = os.getenv('gcp_credentials')
        if not credentials_json:
            logger.warning("No gcp_credentials found, using default credentials")
            return
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(credentials_json)
                self.creds_file_path = f.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_file_path
            logger.info("✅ Successfully set up GCP credentials")
        except Exception as e:
            logger.error(f"❌ Error setting up credentials: {e}")
    
    def cleanup_credentials(self):
        """Clean up temporary credentials file."""
        if self.creds_file_path and os.path.exists(self.creds_file_path):
            try:
                os.unlink(self.creds_file_path)
                logger.info("Cleaned up temporary credentials file")
            except Exception as e:
                logger.warning(f"Could not clean up credentials file: {e}")
    
    def check_prerequisites(self):
        """Check if the voters table exists and has geocoded data."""
        logger.info("Checking prerequisites...")
        
        try:
            table_ref = self.bq_client.dataset(self.dataset_id).table('voters')
            table = self.bq_client.get_table(table_ref)
            logger.info(f"✓ Voters table exists with {table.num_rows:,} rows")
        except NotFound:
            logger.error("✗ Voters table not found!")
            return False
        
        geocoding_query = f"""
        SELECT 
            COUNT(*) as total_voters,
            COUNTIF(latitude IS NOT NULL) as geocoded_voters,
            COUNTIF(addr_residential_street_name IS NOT NULL) as voters_with_street,
            COUNTIF(latitude IS NOT NULL AND addr_residential_street_name IS NOT NULL) as ready_for_summary
        FROM `{self.project_id}.{self.dataset_id}.voters`
        """
        
        try:
            result = self.bq_client.query(geocoding_query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                total = int(row['total_voters'])
                geocoded = int(row['geocoded_voters'])
                with_street = int(row['voters_with_street'])
                ready = int(row['ready_for_summary'])
                
                logger.info(f"✓ Total voters: {total:,}")
                logger.info(f"✓ Geocoded voters: {geocoded:,} ({geocoded/total*100:.1f}%)")
                logger.info(f"✓ Voters with street names: {with_street:,} ({with_street/total*100:.1f}%)")
                logger.info(f"✓ Ready for summary: {ready:,} ({ready/total*100:.1f}%)")
                
                if ready == 0:
                    logger.error("✗ No voters are ready for street summary (need both geocoding and street names)")
                    return False
                    
                return True
        except Exception as e:
            logger.error(f"Error checking prerequisites: {e}")
            return False

def main():
    """Main function to refresh the street party summary table."""
    logger.info("Street Party Summary Refresher")
    logger.info("=" * 50)
    
    refresher = StreetSummaryRefresher()
    
    if not refresher.check_prerequisites():
        logger.error("Prerequisites not met. Cannot refresh street summary.")
        return 1
    
    try:
        refresher.refresh_street_summary()
        logger.info("Street summary refresh completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Failed to refresh street summary: {e}")
        return 1
    finally:
        refresher.cleanup_credentials()

if __name__ == "__main__":
    exit(main())
