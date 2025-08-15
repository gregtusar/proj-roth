#!/usr/bin/env python3
"""
Optimized geocoding pipeline using Google Maps API as primary service.
This script is configured for maximum speed while respecting API limits.
"""

import os
import sys
import time
import logging
from bigquery_geocoding_pipeline import BigQueryVoterGeocodingPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_geocoding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run optimized geocoding pipeline with Google Maps API."""
    
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key:")
        logger.error("export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        return False
    
    logger.info("🚀 Starting optimized geocoding pipeline with Google Maps API")
    logger.info(f"📊 Configuration: 45 req/sec, batch_size=200, max_workers=15, 0.5s delays")
    
    pipeline = BigQueryVoterGeocodingPipeline(
        project_id='proj-roth',
        dataset_id='voter_data',
        google_api_key=google_api_key
    )
    
    try:
        pipeline.create_dataset_if_not_exists()
        
        logger.info("📈 Starting optimized geocoding process...")
        batch_count = 0
        start_time = time.time()
        
        while batch_count < 1000:  # Increased limit for production use
            stats = pipeline.get_geocoding_stats()
            if stats:
                elapsed_time = time.time() - start_time
                rate = stats.get('geocoded_voters', 0) / max(elapsed_time / 60, 1)  # voters per minute
                
                logger.info(f"📊 Progress: {stats.get('completion_percentage', 0)}% complete")
                logger.info(f"📍 Geocoded: {stats.get('geocoded_voters', 0):,} / {stats.get('total_voters', 0):,}")
                logger.info(f"⚡ Rate: {rate:.1f} voters/minute")
                logger.info(f"🗺️  Google: {stats.get('google_geocoded', 0):,}, Census: {stats.get('census_geocoded', 0):,}")
                
                if stats.get('remaining_voters', 0) == 0:
                    logger.info("🎉 Geocoding completed!")
                    break
            
            logger.info(f"🔄 Processing batch {batch_count + 1}...")
            pipeline.geocode_voters_batch(batch_size=200, max_workers=15)
            batch_count += 1
            
            time.sleep(0.5)  # Optimized delay
        
        if batch_count >= 1000:
            logger.info(f"⏸️  Reached batch limit ({batch_count}). Use this script again to continue.")
        
        logger.info("🔄 Refreshing street-level summary data...")
        pipeline.refresh_street_summary()
        logger.info("✅ Pipeline completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in geocoding pipeline: {e}")
        return False
    finally:
        pipeline.cleanup_credentials()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
