#!/usr/bin/env python3
"""
Simple linear geocoding pipeline - no threading, just pure speed.
Processes voters one by one, as fast as possible.
"""

import os
import sys
import time
import logging
import pandas as pd
from typing import Optional, List, Tuple
from google.cloud import bigquery
import googlemaps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bigquery_geocoding_pipeline import GeocodingResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_linear_geocoding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleLinearGeocoder:
    """Dead simple, fast linear geocoding - no threads, no complexity."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data'):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = bigquery.Client(project=project_id)
        
        # Get API key
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.google_api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set!")
        
        # Create optimized Google Maps client
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        self.gmaps = googlemaps.Client(
            key=self.google_api_key,
            requests_session=session,
            timeout=5  # 5 second timeout per request
        )
        
        # Track timing
        self.last_request_time = 0
        self.min_interval = 1.0 / 50  # 50 requests per second
        
        logger.info("🚀 Simple linear geocoder initialized")
    
    def get_voters_batch(self, limit: int = 5000) -> pd.DataFrame:
        """Get a batch of voters needing geocoding."""
        query = f"""
        SELECT 
            id,
            CONCAT(
                IFNULL(addr_residential_street_number, ''),
                ' ',
                IFNULL(addr_residential_street_name, '')
            ) AS address,
            addr_residential_city AS city,
            addr_residential_state AS state,
            CAST(addr_residential_zip_code AS STRING) AS zip_code
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE latitude IS NULL 
        AND addr_residential_street_name IS NOT NULL
        AND addr_residential_city IS NOT NULL
        AND addr_residential_state IS NOT NULL
        LIMIT {limit}
        """
        return self.bq_client.query(query).to_dataframe()
    
    def rate_limit(self):
        """Simple rate limiting - 50 req/sec."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def geocode_address(self, address: str, city: str, state: str, zip_code: str) -> Optional[Tuple[float, float, str]]:
        """Geocode a single address. Returns (lat, lng, accuracy) or None."""
        # Clean up address components
        address = (address or '').strip()
        city = (city or '').strip()
        state = (state or '').strip()
        zip_code = (zip_code or '').strip()
        
        # Skip if missing critical components
        if not city or not state:
            return None
            
        full_address = f"{address}, {city}, {state} {zip_code}".strip()
        
        try:
            self.rate_limit()
            results = self.gmaps.geocode(full_address)
            
            if results and len(results) > 0:
                location = results[0]['geometry']['location']
                accuracy = results[0]['geometry'].get('location_type', 'UNKNOWN')
                return (location['lat'], location['lng'], accuracy)
            
        except Exception as e:
            logger.debug(f"Geocoding failed for {full_address}: {e}")
        
        return None
    
    def update_voters_batch(self, updates: List[Tuple[str, float, float, str]]):
        """Batch update voters in BigQuery. updates = [(voter_id, lat, lng, accuracy), ...]"""
        if not updates:
            return
        
        # Build UPDATE query with CASE statements for efficiency
        when_clauses_lat = []
        when_clauses_lng = []
        when_clauses_acc = []
        voter_ids = []
        
        for voter_id, lat, lng, accuracy in updates:
            voter_ids.append(f"'{voter_id}'")
            when_clauses_lat.append(f"WHEN '{voter_id}' THEN {lat}")
            when_clauses_lng.append(f"WHEN '{voter_id}' THEN {lng}")
            when_clauses_acc.append(f"WHEN '{voter_id}' THEN '{accuracy}'")
        
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.voters`
        SET 
            latitude = CASE id {' '.join(when_clauses_lat)} END,
            longitude = CASE id {' '.join(when_clauses_lng)} END,
            geocoding_accuracy = CASE id {' '.join(when_clauses_acc)} END,
            geocoding_source = 'GOOGLE_MAPS',
            geocoding_timestamp = CURRENT_TIMESTAMP()
        WHERE id IN ({','.join(voter_ids)})
        """
        
        try:
            job = self.bq_client.query(query)
            job.result()
            logger.info(f"✅ Updated {len(updates)} voters")
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            # Fall back to individual updates
            for voter_id, lat, lng, accuracy in updates:
                self.update_single_voter(voter_id, lat, lng, accuracy)
    
    def update_single_voter(self, voter_id: str, lat: float, lng: float, accuracy: str):
        """Update a single voter - fallback method."""
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.voters`
        SET 
            latitude = {lat},
            longitude = {lng},
            geocoding_accuracy = '{accuracy}',
            geocoding_source = 'GOOGLE_MAPS',
            geocoding_timestamp = CURRENT_TIMESTAMP()
        WHERE id = '{voter_id}'
        """
        try:
            self.bq_client.query(query).result()
        except Exception as e:
            logger.error(f"Failed to update voter {voter_id}: {e}")
    
    def run(self):
        """Main execution loop - simple and fast."""
        logger.info("🏃 Starting simple linear geocoding...")
        
        total_processed = 0
        total_geocoded = 0
        start_time = time.time()
        
        while True:
            # Get batch of voters
            voters_df = self.get_voters_batch(5000)
            
            if voters_df.empty:
                logger.info("✅ No more voters to geocode!")
                break
            
            logger.info(f"📦 Processing batch of {len(voters_df)} voters...")
            
            updates = []
            batch_start = time.time()
            
            # Process each voter linearly
            for _, voter in voters_df.iterrows():
                result = self.geocode_address(
                    voter['address'],
                    voter['city'],
                    voter['state'],
                    voter['zip_code']
                )
                
                if result:
                    lat, lng, accuracy = result
                    updates.append((voter['id'], lat, lng, accuracy))
                    total_geocoded += 1
                    
                    # Log progress every 100 successful geocodes
                    if total_geocoded % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = total_geocoded / (elapsed / 60)
                        logger.info(f"📍 Geocoded {total_geocoded} voters | Rate: {rate:.1f}/min")
                
                total_processed += 1
                
                # Update database every 100 successful geocodes
                if len(updates) >= 100:
                    self.update_voters_batch(updates)
                    updates = []
            
            # Update any remaining
            if updates:
                self.update_voters_batch(updates)
            
            # Batch stats
            batch_time = time.time() - batch_start
            batch_rate = len(voters_df) / batch_time
            logger.info(f"⏱️ Batch completed in {batch_time:.1f}s ({batch_rate:.1f} voters/sec)")
            
            # Overall stats
            elapsed_total = time.time() - start_time
            overall_rate = total_geocoded / (elapsed_total / 60)
            success_rate = (total_geocoded / total_processed * 100) if total_processed > 0 else 0
            
            logger.info(f"📊 Progress: {total_geocoded}/{total_processed} geocoded ({success_rate:.1f}% success)")
            logger.info(f"⚡ Overall rate: {overall_rate:.1f} geocodes/min")
            
            # Safety check - limit to reasonable number of batches
            if total_processed >= 100000:
                logger.info("🛑 Reached 100K limit, stopping for safety")
                break
        
        # Final stats
        total_time = time.time() - start_time
        logger.info(f"""
🎉 GEOCODING COMPLETE!
📊 Final Statistics:
   - Total Processed: {total_processed:,}
   - Successfully Geocoded: {total_geocoded:,}
   - Success Rate: {(total_geocoded/total_processed*100) if total_processed > 0 else 0:.1f}%
   - Total Time: {total_time/60:.1f} minutes
   - Average Rate: {total_geocoded/(total_time/60) if total_time > 0 else 0:.1f} geocodes/min
""")

def main():
    """Entry point."""
    try:
        geocoder = SimpleLinearGeocoder()
        geocoder.run()
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())