import pandas as pd
import numpy as np
import time
import json
import os
from typing import Optional, Tuple, Dict, List
import googlemaps
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GeocodingResult:
    """Data class for geocoding results."""
    latitude: Optional[float]
    longitude: Optional[float]
    accuracy: Optional[str]
    source: str
    confidence: float
    standardized_address: Optional[str]
    error: Optional[str] = None

class BigQueryVoterGeocodingPipeline:
    """Pipeline for geocoding voter addresses and storing in BigQuery."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data', 
                 google_api_key: Optional[str] = None):
        """Initialize the geocoding pipeline."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.google_api_key = google_api_key
        self.gmaps_client = None
        
        self.bq_client = bigquery.Client(project=project_id)
        
        if google_api_key:
            self.gmaps_client = googlemaps.Client(key=google_api_key)
        
        self.requests_per_second = 10  # Adjust based on API limits
        self.last_request_time = 0
        
    def create_dataset_if_not_exists(self):
        """Create BigQuery dataset if it doesn't exist."""
        dataset_ref = self.bq_client.dataset(self.dataset_id)
        
        try:
            self.bq_client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset.description = "New Jersey voter registration data with geolocation for political mapping"
            
            dataset = self.bq_client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def geocode_with_google(self, address: str) -> GeocodingResult:
        """Geocode address using Google Maps API."""
        if not self.gmaps_client:
            return GeocodingResult(
                latitude=None, longitude=None, accuracy=None,
                source="GOOGLE_MAPS", confidence=0.0,
                standardized_address=None, error="No API key provided"
            )
        
        try:
            self.rate_limit()
            result = self.gmaps_client.geocode(address)
            
            if result:
                location = result[0]['geometry']['location']
                accuracy = result[0]['geometry']['location_type']
                formatted_address = result[0]['formatted_address']
                
                confidence_map = {
                    'ROOFTOP': 1.0,
                    'RANGE_INTERPOLATED': 0.8,
                    'GEOMETRIC_CENTER': 0.6,
                    'APPROXIMATE': 0.4
                }
                confidence = confidence_map.get(accuracy, 0.2)
                
                return GeocodingResult(
                    latitude=location['lat'],
                    longitude=location['lng'],
                    accuracy=accuracy,
                    source="GOOGLE_MAPS",
                    confidence=confidence,
                    standardized_address=formatted_address
                )
            else:
                return GeocodingResult(
                    latitude=None, longitude=None, accuracy=None,
                    source="GOOGLE_MAPS", confidence=0.0,
                    standardized_address=None, error="No results found"
                )
                
        except Exception as e:
            logger.error(f"Google geocoding error for '{address}': {e}")
            return GeocodingResult(
                latitude=None, longitude=None, accuracy=None,
                source="GOOGLE_MAPS", confidence=0.0,
                standardized_address=None, error=str(e)
            )
    
    def geocode_with_census(self, address: str) -> GeocodingResult:
        """Geocode address using US Census Geocoding API (free alternative)."""
        try:
            self.rate_limit()
            
            url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params = {
                'address': address,
                'benchmark': 'Public_AR_Current',
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result', {}).get('addressMatches'):
                match = data['result']['addressMatches'][0]
                coords = match['coordinates']
                
                return GeocodingResult(
                    latitude=coords['y'],
                    longitude=coords['x'],
                    accuracy="CENSUS_INTERPOLATED",
                    source="US_CENSUS",
                    confidence=0.7,
                    standardized_address=match['matchedAddress']
                )
            else:
                return GeocodingResult(
                    latitude=None, longitude=None, accuracy=None,
                    source="US_CENSUS", confidence=0.0,
                    standardized_address=None, error="No results found"
                )
                
        except Exception as e:
            logger.error(f"Census geocoding error for '{address}': {e}")
            return GeocodingResult(
                latitude=None, longitude=None, accuracy=None,
                source="US_CENSUS", confidence=0.0,
                standardized_address=None, error=str(e)
            )
    
    def geocode_address(self, address: str, fallback_to_census: bool = True) -> GeocodingResult:
        """Geocode an address with fallback options."""
        if self.gmaps_client:
            result = self.geocode_with_google(address)
            if result.latitude is not None:
                return result
        
        if fallback_to_census:
            result = self.geocode_with_census(address)
            if result.latitude is not None:
                return result
        
        return GeocodingResult(
            latitude=None, longitude=None, accuracy=None,
            source="FAILED", confidence=0.0,
            standardized_address=None, error="All geocoding methods failed"
        )
    
    def load_voter_data_from_csv(self, csv_path: str) -> pd.DataFrame:
        """Load voter data from CSV file."""
        logger.info(f"Loading voter data from {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} voter records")
        return df
    
    def create_full_address(self, row: pd.Series) -> str:
        """Create full address string from voter record."""
        parts = []
        
        if pd.notna(row.get('addr_residential_line1')):
            parts.append(str(row['addr_residential_line1']))
        
        if pd.notna(row.get('addr_residential_city')):
            parts.append(str(row['addr_residential_city']))
        
        if pd.notna(row.get('addr_residential_state')):
            parts.append(str(row['addr_residential_state']))
        
        if pd.notna(row.get('addr_residential_zip_code')):
            parts.append(str(int(row['addr_residential_zip_code'])))
        
        return ', '.join(parts)
    
    def import_voters_to_bigquery(self, df: pd.DataFrame, table_name: str = 'voters'):
        """Import voter data to BigQuery."""
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        try:
            logger.info(f"Importing {len(df)} voters to BigQuery table {table_id}")
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Replace existing data
                schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
                autodetect=True
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            logger.info(f"Successfully imported {len(df)} voters to BigQuery")
            
            table = self.bq_client.get_table(table_id)
            logger.info(f"Table {table_id} now has {table.num_rows} rows")
            
        except Exception as e:
            logger.error(f"Error importing voter data to BigQuery: {e}")
            raise
    
    def get_voters_needing_geocoding(self, limit: int = 100) -> pd.DataFrame:
        """Get voters that need geocoding from BigQuery."""
        query = f"""
        SELECT 
            id,
            addr_residential_line1,
            addr_residential_city,
            addr_residential_state,
            addr_residential_zip_code
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE latitude IS NULL
        ORDER BY id
        LIMIT {limit}
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error querying voters needing geocoding: {e}")
            return pd.DataFrame()
    
    def update_voter_geocoding(self, voter_id: str, result: GeocodingResult):
        """Update a single voter's geocoding information in BigQuery."""
        geography_sql = "NULL"
        if result.latitude and result.longitude:
            geography_sql = f"ST_GEOGPOINT({result.longitude}, {result.latitude})"
        
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.voters`
        SET 
            latitude = @latitude,
            longitude = @longitude,
            location = {geography_sql},
            geocoding_accuracy = @accuracy,
            geocoding_source = @source,
            geocoding_confidence = @confidence,
            standardized_address = @standardized_address,
            geocoding_date = CURRENT_TIMESTAMP(),
            updated_at = CURRENT_TIMESTAMP()
        WHERE id = @voter_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("voter_id", "STRING", voter_id),
                bigquery.ScalarQueryParameter("latitude", "FLOAT64", result.latitude),
                bigquery.ScalarQueryParameter("longitude", "FLOAT64", result.longitude),
                bigquery.ScalarQueryParameter("accuracy", "STRING", result.accuracy),
                bigquery.ScalarQueryParameter("source", "STRING", result.source),
                bigquery.ScalarQueryParameter("confidence", "FLOAT64", result.confidence),
                bigquery.ScalarQueryParameter("standardized_address", "STRING", result.standardized_address),
            ]
        )
        
        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            query_job.result()  # Wait for the query to complete
        except Exception as e:
            logger.error(f"Error updating voter {voter_id}: {e}")
            raise
    
    def geocode_voters_batch(self, batch_size: int = 100, max_workers: int = 5):
        """Geocode voters in batches with parallel processing."""
        voters_df = self.get_voters_needing_geocoding(batch_size)
        
        if voters_df.empty:
            logger.info("No voters found that need geocoding")
            return
        
        logger.info(f"Geocoding {len(voters_df)} voters")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_voter = {}
            for _, voter in voters_df.iterrows():
                address = self.create_full_address(voter)
                future = executor.submit(self.geocode_address, address)
                future_to_voter[future] = voter
            
            for future in as_completed(future_to_voter):
                voter = future_to_voter[future]
                try:
                    result = future.result()
                    
                    self.update_voter_geocoding(voter['id'], result)
                    
                    if result.latitude:
                        logger.info(f"Geocoded {voter['id']}: {result.latitude}, {result.longitude}")
                    else:
                        logger.warning(f"Failed to geocode {voter['id']}: {result.error}")
                        
                except Exception as e:
                    logger.error(f"Error processing voter {voter['id']}: {e}")
    
    def refresh_street_summary(self):
        """Refresh the street-level party summary table."""
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
            
            ST_CENTROID(ST_UNION_AGG(location)) as street_center_location,
            ST_X(ST_CENTROID(ST_UNION_AGG(location))) as street_center_longitude,
            ST_Y(ST_CENTROID(ST_UNION_AGG(location))) as street_center_latitude,
            
            CURRENT_TIMESTAMP() as last_updated
            
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE addr_residential_street_name IS NOT NULL 
          AND location IS NOT NULL
        GROUP BY addr_residential_street_name, addr_residential_city, county_name, addr_residential_zip_code
        HAVING COUNT(*) >= 3
        """
        
        try:
            query_job = self.bq_client.query(query)
            query_job.result()
            logger.info("Street party summary table refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing street summary: {e}")
            raise
    
    def get_geocoding_stats(self) -> Dict:
        """Get statistics on geocoding progress."""
        query = f"""
        SELECT 
            COUNT(*) as total_voters,
            COUNTIF(latitude IS NOT NULL) as geocoded_voters,
            COUNTIF(latitude IS NULL) as remaining_voters,
            ROUND(COUNTIF(latitude IS NOT NULL) * 100.0 / COUNT(*), 2) as completion_pct,
            COUNTIF(geocoding_source = 'GOOGLE_MAPS') as google_geocoded,
            COUNTIF(geocoding_source = 'US_CENSUS') as census_geocoded,
            AVG(geocoding_confidence) as avg_confidence
        FROM `{self.project_id}.{self.dataset_id}.voters`
        """
        
        try:
            result = self.bq_client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                return {
                    'total_voters': int(row['total_voters']),
                    'geocoded_voters': int(row['geocoded_voters']),
                    'remaining_voters': int(row['remaining_voters']),
                    'completion_percentage': float(row['completion_pct']),
                    'google_geocoded': int(row['google_geocoded']),
                    'census_geocoded': int(row['census_geocoded']),
                    'average_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting geocoding stats: {e}")
            return {}

def main():
    """Example usage of the BigQuery geocoding pipeline."""
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')  # Set in environment
    pipeline = BigQueryVoterGeocodingPipeline(
        project_id='proj-roth',
        dataset_id='voter_data',
        google_api_key=google_api_key
    )
    
    pipeline.create_dataset_if_not_exists()
    
    df = pipeline.load_voter_data_from_csv('/home/ubuntu/export-20250729.csv')
    pipeline.import_voters_to_bigquery(df)
    
    while True:
        stats = pipeline.get_geocoding_stats()
        if stats:
            logger.info(f"Geocoding progress: {stats['completion_percentage']}% complete")
            
            if stats['remaining_voters'] == 0:
                logger.info("Geocoding completed!")
                break
        
        pipeline.geocode_voters_batch(batch_size=100)
        
        time.sleep(1)
    
    pipeline.refresh_street_summary()
    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
