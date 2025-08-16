#!/usr/bin/env python3
"""
Ultra-simple linear geocoding pipeline - no threading, no complexity, just pure sequential processing.
Processes voters one by one, as fast as possible without any threading or batch complexity.
"""

import os
import sys
import time
import logging
import pandas as pd
from typing import Optional
from google.cloud import bigquery
import googlemaps

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bigquery_geocoding_pipeline import BigQueryVoterGeocodingPipeline, GeocodingResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_simple_linear_geocoding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UltraSimpleLinearGeocoder(BigQueryVoterGeocodingPipeline):
    """Ultra-simple linear geocoding - inherits proven methods, removes all complexity."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data', google_api_key: Optional[str] = None):
        super().__init__(project_id, dataset_id, google_api_key)
        
        self.last_request_time = 0
        self.min_interval = 1.0 / 50  # 50 requests per second max
        
        logger.info("🚀 Ultra-simple linear geocoder initialized")
    
    def simple_rate_limit(self):
        """Simple rate limiting - 50 req/sec max."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def run_linear_geocoding(self, max_voters: int = 10000):
        """Main execution loop - ultra-simple linear processing."""
        logger.info("🏃 Starting ultra-simple linear geocoding...")
        
        total_processed = 0
        total_geocoded = 0
        start_time = time.time()
        
        while total_processed < max_voters:
            voters_df = self.get_voters_needing_geocoding(limit=100)
            
            if voters_df.empty:
                logger.info("✅ No more voters to geocode!")
                break
            
            logger.info(f"📦 Processing {len(voters_df)} voters linearly...")
            
            for _, voter in voters_df.iterrows():
                try:
                    self.simple_rate_limit()
                    
                    address_parts = []
                    if voter.get('addr_residential_street_number'):
                        address_parts.append(str(voter['addr_residential_street_number']))
                    if voter.get('addr_residential_street_name'):
                        address_parts.append(str(voter['addr_residential_street_name']))
                    if voter.get('addr_residential_city'):
                        address_parts.append(str(voter['addr_residential_city']))
                    if voter.get('addr_residential_state'):
                        address_parts.append(str(voter['addr_residential_state']))
                    if voter.get('addr_residential_zip_code'):
                        address_parts.append(str(voter['addr_residential_zip_code']))
                    
                    full_address = ', '.join(address_parts)
                    
                    result = self.geocode_address(full_address)
                    
                    if result and result.latitude is not None:
                        self.update_voter_geocoding(voter['id'], result)
                        total_geocoded += 1
                        
                        if total_geocoded % 50 == 0:
                            elapsed = time.time() - start_time
                            rate = total_geocoded / (elapsed / 60) if elapsed > 0 else 0
                            logger.info(f"📍 Geocoded {total_geocoded} voters | Rate: {rate:.1f}/min")
                    
                    total_processed += 1
                    
                    if total_processed % 100 == 0:
                        elapsed = time.time() - start_time
                        overall_rate = total_processed / (elapsed / 60) if elapsed > 0 else 0
                        success_rate = (total_geocoded / total_processed * 100) if total_processed > 0 else 0
                        logger.info(f"📊 Progress: {total_geocoded}/{total_processed} ({success_rate:.1f}% success) | {overall_rate:.1f} voters/min")
                
                except Exception as e:
                    logger.error(f"❌ Error processing voter {voter['id']}: {e}")
                    total_processed += 1
                    continue
        
        # Final stats
        total_time = time.time() - start_time
        logger.info(f"""
🎉 LINEAR GEOCODING COMPLETE!
📊 Final Statistics:
   - Total Processed: {total_processed:,}
   - Successfully Geocoded: {total_geocoded:,}
   - Success Rate: {(total_geocoded/total_processed*100) if total_processed > 0 else 0:.1f}%
   - Total Time: {total_time/60:.1f} minutes
   - Average Rate: {total_geocoded/(total_time/60) if total_time > 0 else 0:.1f} geocodes/min
""")
        
        return {
            'total_processed': total_processed,
            'total_geocoded': total_geocoded,
            'success_rate': (total_geocoded/total_processed*100) if total_processed > 0 else 0,
            'total_time_minutes': total_time/60,
            'geocodes_per_minute': total_geocoded/(total_time/60) if total_time > 0 else 0
        }

def main():
    """Entry point for ultra-simple linear geocoding."""
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key:")
        logger.error("export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        logger.error("See docs/README_google_maps_setup.md for setup instructions")
        return 1
    
    gcp_credentials = os.getenv('GCP_CREDENTIALS')
    if not gcp_credentials:
        logger.error("❌ GCP_CREDENTIALS environment variable not set!")
        logger.error("Please set your GCP service account credentials:")
        logger.error("export GCP_CREDENTIALS='your_service_account_json_here'")
        logger.error("See docs/README.md for setup instructions")
        return 1
    
    logger.info("✅ Environment variables validated successfully")
    logger.info(f"📊 Google Maps API key: {google_api_key[:10]}... ({len(google_api_key)} chars)")
    
    try:
        geocoder = UltraSimpleLinearGeocoder(google_api_key=google_api_key)
        
        logger.info("🧪 Testing with small batch of 50 voters...")
        results = geocoder.run_linear_geocoding(max_voters=50)
        
        if results['total_geocoded'] > 0:
            logger.info("✅ Test successful! Linear geocoding is working.")
            logger.info("💡 To process more voters, increase max_voters parameter in run_linear_geocoding()")
        else:
            logger.warning("⚠️ No voters were geocoded. Check API key validity and data availability.")
            logger.warning("💡 Run diagnose_geocoding_auth.py for detailed diagnostics")
        
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
