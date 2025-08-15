#!/usr/bin/env python3
"""
Ultra-fast geocoding pipeline with optimized rate limiting and batch processing.
This script addresses the bottlenecks in the current pipeline:
1. Global rate limiting instead of per-thread
2. Batch BigQuery updates instead of individual updates
3. Optimized connection pooling
4. Higher Google Maps API rate limits
"""

import os
import sys
import time
import logging
import threading
from queue import Queue
from typing import List, Dict, Tuple
import pandas as pd
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bigquery_geocoding_pipeline import BigQueryVoterGeocodingPipeline, GeocodingResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_fast_geocoding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GlobalRateLimiter:
    """Global rate limiter shared across all threads."""
    
    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def acquire(self):
        """Acquire permission to make a request, blocking if necessary."""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_request_time = time.time()

class UltraFastGeocodingPipeline(BigQueryVoterGeocodingPipeline):
    """Ultra-fast geocoding pipeline with optimized performance."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data', 
                 google_api_key: str = None):
        super().__init__(project_id, dataset_id, google_api_key)
        
        self.requests_per_second = 49
        self.global_rate_limiter = GlobalRateLimiter(self.requests_per_second)
        
        logger.info(f"🚀 Ultra-fast pipeline initialized: {self.requests_per_second} req/sec")
    
    def rate_limit(self):
        """Use global rate limiter instead of per-thread sleep."""
        self.global_rate_limiter.acquire()
    
    def batch_update_voters(self, voter_results: List[Tuple[str, GeocodingResult]]):
        """Update multiple voters in a single BigQuery operation."""
        if not voter_results:
            return
        
        cases_lat = []
        cases_lng = []
        cases_accuracy = []
        cases_source = []
        cases_address = []
        voter_ids = []
        
        for voter_id, result in voter_results:
            if result.latitude is not None:
                voter_ids.append(f"'{voter_id}'")
                cases_lat.append(f"WHEN '{voter_id}' THEN {result.latitude}")
                cases_lng.append(f"WHEN '{voter_id}' THEN {result.longitude}")
                
                accuracy_val = (result.accuracy or '').replace("'", "''").replace('"', '""')
                cases_accuracy.append(f"WHEN '{voter_id}' THEN '{accuracy_val}'")
                
                source_val = (result.source or '').replace("'", "''").replace('"', '""')
                cases_source.append(f"WHEN '{voter_id}' THEN '{source_val}'")
                
                standardized_addr = (result.standardized_address or '')
                standardized_addr = standardized_addr.replace("'", "''").replace('"', '""').replace('\\', '\\\\')
                standardized_addr = standardized_addr.replace(';', '').replace('--', '').replace('/*', '').replace('*/', '')
                cases_address.append(f"WHEN '{voter_id}' THEN '{standardized_addr}'")
        
        if not voter_ids:
            return
        
        lat_cases = ' '.join(cases_lat) if cases_lat else 'NULL'
        lng_cases = ' '.join(cases_lng) if cases_lng else 'NULL'
        accuracy_cases = ' '.join(cases_accuracy) if cases_accuracy else 'NULL'
        source_cases = ' '.join(cases_source) if cases_source else 'NULL'
        address_cases = ' '.join(cases_address) if cases_address else 'NULL'
        
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.voters`
        SET 
            latitude = CASE id {lat_cases} END,
            longitude = CASE id {lng_cases} END,
            geocoding_accuracy = CASE id {accuracy_cases} END,
            geocoding_source = CASE id {source_cases} END,
            geocoding_timestamp = CURRENT_TIMESTAMP(),
            full_address = CASE id {address_cases} END
        WHERE id IN ({', '.join(voter_ids)})
        """
        
        try:
            query_job = self.bq_client.query(query)
            query_job.result()
            logger.info(f"✅ Batch updated {len(voter_ids)} voters")
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            for voter_id, result in voter_results:
                try:
                    self.update_voter_geocoding(voter_id, result)
                except Exception as individual_error:
                    logger.error(f"❌ Individual update failed for {voter_id}: {individual_error}")
    
    def ultra_fast_geocode_batch(self, batch_size: int = 500, max_workers: int = 25):
        """Ultra-fast batch geocoding with optimized settings."""
        voters_df = self.get_voters_needing_geocoding(batch_size)
        
        if voters_df.empty:
            logger.info("No voters found that need geocoding")
            return
        
        logger.info(f"🔥 Ultra-fast geocoding {len(voters_df)} voters with {max_workers} workers")
        
        results_queue = Queue()
        
        def geocode_worker(voter_row):
            """Worker function for geocoding."""
            try:
                address = self.create_full_address(voter_row)
                result = self.geocode_address(address, fallback_to_census=False)
                return (voter_row['id'], result)
            except Exception as e:
                logger.error(f"❌ Geocoding error for {voter_row['id']}: {e}")
                return (voter_row['id'], GeocodingResult(
                    latitude=None, longitude=None, accuracy=None,
                    source="ERROR", confidence=0.0,
                    standardized_address=None, error=str(e)
                ))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_voter = {
                executor.submit(geocode_worker, voter): voter 
                for _, voter in voters_df.iterrows()
            }
            
            batch_results = []
            successful_geocodes = 0
            
            for future in as_completed(future_to_voter):
                voter_id, result = future.result()
                batch_results.append((voter_id, result))
                
                if result.latitude is not None:
                    successful_geocodes += 1
                    logger.info(f"✅ {voter_id}: {result.latitude}, {result.longitude}")
                
                if len(batch_results) >= 50:
                    self.batch_update_voters(batch_results)
                    batch_results = []
            
            if batch_results:
                self.batch_update_voters(batch_results)
            
            logger.info(f"🎯 Batch complete: {successful_geocodes}/{len(voters_df)} successful geocodes")

def main():
    """Run ultra-fast geocoding pipeline."""
    
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        return False
    
    logger.info("🚀 Starting ULTRA-FAST geocoding pipeline")
    logger.info("📊 Configuration: 49 req/sec, batch_size=500, max_workers=25, batch BigQuery updates")
    
    pipeline = UltraFastGeocodingPipeline(
        project_id='proj-roth',
        dataset_id='voter_data',
        google_api_key=google_api_key
    )
    
    try:
        pipeline.create_dataset_if_not_exists()
        
        logger.info("🔥 Starting ultra-fast geocoding process...")
        batch_count = 0
        start_time = time.time()
        
        while batch_count < 2000:
            stats = pipeline.get_geocoding_stats()
            if stats:
                elapsed_time = time.time() - start_time
                rate = stats.get('geocoded_voters', 0) / max(elapsed_time / 60, 1)
                
                logger.info(f"📊 Progress: {stats.get('completion_percentage', 0)}% complete")
                logger.info(f"📍 Geocoded: {stats.get('geocoded_voters', 0):,} / {stats.get('total_voters', 0):,}")
                logger.info(f"⚡ Rate: {rate:.1f} voters/minute")
                logger.info(f"🗺️  Google: {stats.get('google_geocoded', 0):,}, Census: {stats.get('census_geocoded', 0):,}")
                
                if stats.get('remaining_voters', 0) == 0:
                    logger.info("🎉 Ultra-fast geocoding completed!")
                    break
            
            logger.info(f"🔄 Processing ultra-fast batch {batch_count + 1}...")
            pipeline.ultra_fast_geocode_batch(batch_size=500, max_workers=25)
            batch_count += 1
            
            time.sleep(0.1)
        
        if batch_count >= 2000:
            logger.info(f"⏸️  Reached batch limit ({batch_count}). Continue with another run.")
        
        logger.info("🔄 Refreshing street-level summary data...")
        pipeline.refresh_street_summary()
        logger.info("✅ Ultra-fast pipeline completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in ultra-fast geocoding pipeline: {e}")
        return False
    finally:
        pipeline.cleanup_credentials()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
