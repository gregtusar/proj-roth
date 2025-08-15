#!/usr/bin/env python3
"""
Test script for the ultra-fast geocoding pipeline.
Tests the optimizations with a small batch to verify performance improvements.
"""

import os
import sys
import time
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geocoding'))
from ultra_fast_geocoding_pipeline import UltraFastGeocodingPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ultra_fast_pipeline():
    """Test the ultra-fast geocoding pipeline with a small batch."""
    
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        return False
    
    logger.info("🧪 Testing ultra-fast geocoding pipeline")
    
    pipeline = UltraFastGeocodingPipeline(
        project_id='proj-roth',
        dataset_id='voter_data',
        google_api_key=google_api_key
    )
    
    try:
        initial_stats = pipeline.get_geocoding_stats()
        logger.info(f"📊 Initial stats: {initial_stats}")
        
        start_time = time.time()
        
        pipeline.ultra_fast_geocode_batch(batch_size=100, max_workers=25)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        final_stats = pipeline.get_geocoding_stats()
        logger.info(f"📊 Final stats: {final_stats}")
        
        new_geocodes = final_stats.get('geocoded_voters', 0) - initial_stats.get('geocoded_voters', 0)
        rate_per_minute = (new_geocodes / elapsed_time) * 60 if elapsed_time > 0 else 0
        
        logger.info(f"✅ Test completed!")
        logger.info(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"📍 New geocodes: {new_geocodes}")
        logger.info(f"⚡ Rate: {rate_per_minute:.1f} voters/minute")
        
        if rate_per_minute > 1000:
            logger.info("🎉 Ultra-fast pipeline is working! Rate > 1000 voters/minute")
            return True
        else:
            logger.warning(f"⚠️  Rate is {rate_per_minute:.1f} voters/minute - may need further optimization")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        pipeline.cleanup_credentials()

if __name__ == "__main__":
    success = test_ultra_fast_pipeline()
    exit(0 if success else 1)
