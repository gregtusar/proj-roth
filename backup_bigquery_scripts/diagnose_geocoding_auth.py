#!/usr/bin/env python3
"""
Diagnostic script to check geocoding authentication and API setup.
This helps identify why the ultra_simple_linear_geocoding.py script geocoded 0 voters.
"""

import os
import sys
import logging
from google.cloud import bigquery
import googlemaps

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'geocoding'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment variables...")
    
    gcp_creds = os.getenv('GCP_CREDENTIALS')
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if gcp_creds:
        logger.info("✅ GCP_CREDENTIALS is set")
    else:
        logger.warning("❌ GCP_CREDENTIALS is not set")
    
    if google_api_key:
        logger.info("✅ GOOGLE_MAPS_API_KEY is set")
        logger.info(f"📊 API key length: {len(google_api_key)} characters")
        logger.info(f"📊 API key starts with: {google_api_key[:10]}...")
    else:
        logger.warning("❌ GOOGLE_MAPS_API_KEY is not set")
    
    return gcp_creds, google_api_key

def test_bigquery_connection():
    """Test BigQuery connection."""
    logger.info("🔍 Testing BigQuery connection...")
    
    try:
        client = bigquery.Client()
        logger.info(f"✅ BigQuery client created for project: {client.project}")
        
        query = "SELECT COUNT(*) as voter_count FROM `proj-roth.voter_data.voters` LIMIT 1"
        result = client.query(query).result()
        
        for row in result:
            logger.info(f"📊 Total voters in database: {row.voter_count:,}")
        
        query = "SELECT COUNT(*) as need_geocoding FROM `proj-roth.voter_data.voters` WHERE latitude IS NULL LIMIT 1"
        result = client.query(query).result()
        
        for row in result:
            logger.info(f"📊 Voters needing geocoding: {row.need_geocoding:,}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery connection failed: {e}")
        return False

def test_google_maps_api(api_key):
    """Test Google Maps API connection."""
    if not api_key:
        logger.warning("⚠️ Cannot test Google Maps API - no API key provided")
        return False
    
    logger.info("🔍 Testing Google Maps API...")
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
        result = gmaps.geocode(test_address)
        
        if result:
            location = result[0]['geometry']['location']
            logger.info(f"✅ Google Maps API working - test geocode successful")
            logger.info(f"📍 Test result: {location['lat']}, {location['lng']}")
            return True
        else:
            logger.error("❌ Google Maps API returned empty result")
            return False
            
    except Exception as e:
        logger.error(f"❌ Google Maps API test failed: {e}")
        return False

def test_geocoding_pipeline():
    """Test the actual geocoding pipeline components."""
    logger.info("🔍 Testing geocoding pipeline components...")
    
    try:
        from ultra_simple_linear_geocoding import UltraSimpleLinearGeocoder
        
        geocoder = UltraSimpleLinearGeocoder()
        logger.info("✅ UltraSimpleLinearGeocoder created successfully")
        
        voters_df = geocoder.get_voters_needing_geocoding(limit=5)
        logger.info(f"📊 Found {len(voters_df)} voters needing geocoding (limit=5)")
        
        if not voters_df.empty:
            sample_voter = voters_df.iloc[0]
            logger.info(f"📋 Sample voter ID: {sample_voter['id']}")
            
            address_parts = []
            for field in ['addr_residential_street_number', 'addr_residential_street_name', 
                         'addr_residential_city', 'addr_residential_state', 'addr_residential_zip_code']:
                if sample_voter.get(field):
                    address_parts.append(str(sample_voter[field]))
            
            full_address = ', '.join(address_parts)
            logger.info(f"📍 Sample address: {full_address}")
            
            result = geocoder.geocode_address(full_address)
            if result and result.latitude:
                logger.info(f"✅ Geocoding test successful: {result.latitude}, {result.longitude}")
                logger.info(f"📊 Source: {result.source}, Accuracy: {result.accuracy}")
            else:
                logger.error("❌ Geocoding test failed - no result returned")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Geocoding pipeline test failed: {e}")
        return False

def main():
    """Run all diagnostic tests."""
    logger.info("🔬 Geocoding Authentication Diagnostics")
    logger.info("=" * 50)
    
    gcp_creds, google_api_key = check_environment_variables()
    
    bq_success = test_bigquery_connection()
    
    gmaps_success = test_google_maps_api(google_api_key)
    
    pipeline_success = test_geocoding_pipeline()
    
    logger.info("\n📋 DIAGNOSTIC SUMMARY:")
    logger.info(f"  GCP Credentials: {'✅' if gcp_creds else '❌'}")
    logger.info(f"  Google Maps API Key: {'✅' if google_api_key else '❌'}")
    logger.info(f"  BigQuery Connection: {'✅' if bq_success else '❌'}")
    logger.info(f"  Google Maps API: {'✅' if gmaps_success else '❌'}")
    logger.info(f"  Geocoding Pipeline: {'✅' if pipeline_success else '❌'}")
    
    if all([gcp_creds, google_api_key, bq_success, gmaps_success, pipeline_success]):
        logger.info("\n🎉 All systems operational! The linear geocoding script should work.")
    else:
        logger.info("\n⚠️ Issues detected. Fix the above problems before running geocoding.")

if __name__ == "__main__":
    main()
