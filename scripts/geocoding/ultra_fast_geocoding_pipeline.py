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
import random
from queue import Queue
from typing import List, Dict, Tuple, Optional
import pandas as pd
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import bigquery

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
                 google_api_key: Optional[str] = None):
        super().__init__(project_id, dataset_id, google_api_key)
        
        self.requests_per_second = 50
        self.global_rate_limiter = GlobalRateLimiter(self.requests_per_second)
        
        logger.info(f"🚀 Ultra-fast pipeline initialized: {self.requests_per_second} req/sec")
    
    def rate_limit(self):
        """Use global rate limiter instead of per-thread sleep."""
        self.global_rate_limiter.acquire()
    
    def batch_update_voters(self, voter_results: List[Tuple[str, GeocodingResult]]):
        """Update multiple voters using BigQuery bulk operations for maximum performance."""
        if not voter_results:
            return
        
        valid_results = [(voter_id, result) for voter_id, result in voter_results 
                        if result.latitude is not None]
        
        if not valid_results:
            logger.info("No valid geocoding results to update")
            return
        
        logger.info(f"🚀 Bulk updating {len(valid_results)} voters using BigQuery bulk operations")
        
        try:
            temp_table_id = f"temp_geocoding_updates_{int(time.time() * 1000)}"
            temp_table_ref = f"`{self.project_id}.{self.dataset_id}.{temp_table_id}`"
            
            rows_to_insert = []
            for voter_id, result in valid_results:
                rows_to_insert.append({
                    'voter_id': voter_id,
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'geocoding_accuracy': result.accuracy or '',
                    'geocoding_source': result.source,
                    'geocoding_timestamp': 'CURRENT_TIMESTAMP()',
                    'full_address': result.standardized_address or ''
                })
            
            from google.cloud import bigquery
            schema = [
                bigquery.SchemaField("voter_id", "STRING"),
                bigquery.SchemaField("latitude", "FLOAT64"),
                bigquery.SchemaField("longitude", "FLOAT64"),
                bigquery.SchemaField("geocoding_accuracy", "STRING"),
                bigquery.SchemaField("geocoding_source", "STRING"),
                bigquery.SchemaField("geocoding_timestamp", "STRING"),
                bigquery.SchemaField("full_address", "STRING"),
            ]
            
            temp_table = bigquery.Table(temp_table_ref, schema=schema)
            temp_table = self.bq_client.create_table(temp_table)
            logger.info(f"📊 Created temporary table: {temp_table_id}")
            
            errors = self.bq_client.insert_rows_json(temp_table, rows_to_insert)
            if errors:
                logger.error(f"❌ Failed to insert into temp table: {errors}")
                return
            
            logger.info(f"📥 Inserted {len(rows_to_insert)} rows into temporary table")
            
            merge_query = f"""
            MERGE `{self.project_id}.{self.dataset_id}.voters` AS target
            USING {temp_table_ref} AS source
            ON target.id = source.voter_id
            WHEN MATCHED THEN
              UPDATE SET
                latitude = source.latitude,
                longitude = source.longitude,
                geocoding_accuracy = source.geocoding_accuracy,
                geocoding_source = source.geocoding_source,
                geocoding_timestamp = CURRENT_TIMESTAMP(),
                full_address = source.full_address
            """
            
            job = self.bq_client.query(merge_query)
            job.result()  # Wait for completion
            
            logger.info(f"✅ Bulk updated {len(valid_results)} voters successfully")
            
            self.bq_client.delete_table(temp_table)
            logger.info(f"🗑️ Cleaned up temporary table: {temp_table_id}")
            
        except Exception as e:
            logger.error(f"❌ Bulk update failed: {e}")
            logger.info("🔄 Falling back to individual updates...")
            successful_updates = 0
            for voter_id, result in valid_results:
                if self._update_voter_with_retry(voter_id, result):
                    successful_updates += 1
            logger.info(f"✅ Fallback completed: {successful_updates}/{len(valid_results)} voters updated")
    
    def _update_voter_with_retry(self, voter_id: str, result: GeocodingResult, max_retries: int = 3) -> bool:
        """Update a single voter with exponential backoff retry for concurrency issues."""
        for attempt in range(max_retries + 1):
            try:
                self.update_voter_geocoding(voter_id, result)
                return True
            except Exception as e:
                error_msg = str(e).lower()
                
                if "concurrent update" in error_msg or "serialize access" in error_msg:
                    if attempt < max_retries:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"⚠️ Concurrency conflict for {voter_id}, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Max retries exceeded for {voter_id} due to concurrency: {e}")
                        return False
                else:
                    logger.error(f"❌ Individual update failed for {voter_id}: {e}")
                    return False
        
        return False
    
    def ultra_fast_geocode_batch(self, batch_size: int = 1000, max_workers: int = 40):
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
                
                if len(batch_results) >= 200:
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
    logger.info("📊 Configuration: 50 req/sec, batch_size=1000, max_workers=40, optimized for maximum throughput")
    
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
            pipeline.ultra_fast_geocode_batch(batch_size=1000, max_workers=40)
            batch_count += 1
            
        
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
