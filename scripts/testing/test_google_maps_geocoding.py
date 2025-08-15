#!/usr/bin/env python3
"""
Test script to verify Google Maps API geocoding with small batch.
"""

import os
import sys
import time
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geocoding'))
from bigquery_geocoding_pipeline import BigQueryVoterGeocodingPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test Google Maps API geocoding with a small batch."""
    
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key first:")
        logger.error("export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        return False
    
    logger.info("🧪 Testing Google Maps API geocoding with small batch...")
    
    pipeline = BigQueryVoterGeocodingPipeline(
        project_id='proj-roth',
        dataset_id='voter_data',
        google_api_key=google_api_key
    )
    
    try:
        initial_stats = pipeline.get_geocoding_stats()
        logger.info(f"📊 Initial stats: {initial_stats.get('geocoded_voters', 0):,} geocoded voters")
        
        start_time = time.time()
        logger.info("🔄 Processing test batch of 50 voters...")
        pipeline.geocode_voters_batch(batch_size=50, max_workers=5)
        
        final_stats = pipeline.get_geocoding_stats()
        elapsed_time = time.time() - start_time
        
        geocoded_count = final_stats.get('geocoded_voters', 0) - initial_stats.get('geocoded_voters', 0)
        google_count = final_stats.get('google_geocoded', 0) - initial_stats.get('google_geocoded', 0)
        
        logger.info(f"✅ Test completed in {elapsed_time:.1f} seconds")
        logger.info(f"📍 Geocoded {geocoded_count} new voters")
        logger.info(f"🗺️  Google Maps API used for {google_count} geocodes")
        logger.info(f"⚡ Rate: {geocoded_count / max(elapsed_time / 60, 1):.1f} voters/minute")
        
        if google_count > 0:
            logger.info("🎉 Google Maps API is working correctly!")
            return True
        else:
            logger.warning("⚠️  No Google Maps API geocodes - check API key and billing")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        return False
    finally:
        pipeline.cleanup_credentials()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
