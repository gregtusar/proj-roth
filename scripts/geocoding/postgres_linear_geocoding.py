#!/usr/bin/env python3
"""
Simple linear geocoding pipeline for PostgreSQL - no threading, no complexity.
Replaces BigQuery-based geocoding with PostgreSQL operations.
"""

import os
import sys
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import googlemaps
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_linear_geocoding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GeocodingResult:
    """Result of a geocoding operation."""
    latitude: Optional[float]
    longitude: Optional[float]
    accuracy: Optional[str]
    source: str
    confidence: float
    standardized_address: Optional[str]
    error: Optional[str] = None

class PostgresLinearGeocoder:
    """Simple linear geocoding pipeline using PostgreSQL."""
    
    def __init__(self, 
                 google_api_key: Optional[str] = None,
                 pg_host: str = 'localhost',
                 pg_port: int = 5432,
                 pg_database: str = 'voter_data',
                 pg_user: str = 'postgres',
                 pg_password: str = None):
        
        self.google_api_key = google_api_key
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_database = pg_database
        self.pg_user = pg_user
        self.pg_password = pg_password or os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        self.pg_conn = None
        self.gmaps_client = None
        self.last_request_time = 0
        self.min_interval = 1.0 / 50  # 50 requests per second max
        
        logger.info("🚀 PostgreSQL linear geocoder initialized")
    
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password,
                cursor_factory=RealDictCursor
            )
            self.pg_conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to PostgreSQL: {e}")
            return False
    
    def setup_google_maps(self):
        """Setup Google Maps client."""
        if not self.google_api_key:
            logger.error("Google Maps API key not provided")
            return False
        
        try:
            self.gmaps_client = googlemaps.Client(key=self.google_api_key)
            logger.info("✅ Google Maps client initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up Google Maps client: {e}")
            return False
    
    def simple_rate_limit(self):
        """Simple rate limiting - 50 req/sec max."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def get_voters_needing_geocoding(self, limit: int = 100) -> List[Dict]:
        """Get voters that need geocoding from PostgreSQL."""
        query = """
        SELECT 
            id,
            addr_residential_street_number,
            addr_residential_street_name,
            addr_residential_city,
            addr_residential_state,
            addr_residential_zip_code
        FROM voters
        WHERE latitude IS NULL
        ORDER BY id
        LIMIT %s
        """
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(query, (limit,))
                voters = cursor.fetchall()
                return [dict(voter) for voter in voters]
        except Exception as e:
            logger.error(f"Error querying voters needing geocoding: {e}")
            return []
    
    def create_full_address(self, voter: Dict) -> str:
        """Create full address string from voter record."""
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
        
        return ', '.join(address_parts)
    
    def geocode_address(self, address: str) -> GeocodingResult:
        """Geocode an address using Google Maps API."""
        if not self.gmaps_client:
            return GeocodingResult(
                latitude=None, longitude=None, accuracy=None,
                source="ERROR", confidence=0.0,
                standardized_address=None, error="Google Maps client not initialized"
            )
        
        try:
            self.simple_rate_limit()
            
            result = self.gmaps_client.geocode(address)
            
            if result and len(result) > 0:
                location = result[0]['geometry']['location']
                formatted_address = result[0]['formatted_address']
                location_type = result[0]['geometry'].get('location_type', 'UNKNOWN')
                
                return GeocodingResult(
                    latitude=location['lat'],
                    longitude=location['lng'],
                    accuracy=location_type,
                    source="GOOGLE_MAPS",
                    confidence=1.0,
                    standardized_address=formatted_address
                )
            else:
                return GeocodingResult(
                    latitude=None, longitude=None, accuracy=None,
                    source="FAILED", confidence=0.0,
                    standardized_address=None, error="No results found"
                )
                
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return GeocodingResult(
                latitude=None, longitude=None, accuracy=None,
                source="ERROR", confidence=0.0,
                standardized_address=None, error=str(e)
            )
    
    def update_voter_geocoding(self, voter_id: str, result: GeocodingResult):
        """Update a single voter's geocoding information in PostgreSQL."""
        query = """
        UPDATE voters
        SET 
            latitude = %s,
            longitude = %s,
            geocoding_accuracy = %s,
            geocoding_source = %s,
            geocoding_timestamp = CURRENT_TIMESTAMP,
            full_address = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(query, (
                    result.latitude,
                    result.longitude,
                    result.accuracy or '',
                    result.source,
                    result.standardized_address or '',
                    voter_id
                ))
        except Exception as e:
            logger.error(f"Error updating voter {voter_id}: {e}")
            raise
    
    def get_geocoding_stats(self) -> Dict:
        """Get statistics on geocoding progress."""
        query = """
        SELECT 
            COUNT(*) as total_voters,
            COUNT(latitude) as geocoded_voters,
            COUNT(*) - COUNT(latitude) as remaining_voters,
            ROUND(COUNT(latitude) * 100.0 / COUNT(*), 2) as completion_pct,
            COUNT(CASE WHEN geocoding_source = 'GOOGLE_MAPS' THEN 1 END) as google_geocoded
        FROM voters
        """
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting geocoding stats: {e}")
            return {}
    
    def refresh_street_summary(self):
        """Refresh the street-level party summary table."""
        logger.info("🔄 Refreshing street party summary...")
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("SELECT refresh_street_party_summary()")
            logger.info("✅ Street party summary refreshed successfully")
        except Exception as e:
            logger.error(f"❌ Error refreshing street summary: {e}")
            raise
    
    def run_linear_geocoding(self, max_voters: int = 10000):
        """Main execution loop - ultra-simple linear processing."""
        logger.info("🏃 Starting PostgreSQL linear geocoding...")
        
        total_processed = 0
        total_geocoded = 0
        start_time = time.time()
        
        while total_processed < max_voters:
            voters = self.get_voters_needing_geocoding(limit=100)
            
            if not voters:
                logger.info("✅ No more voters to geocode!")
                break
            
            logger.info(f"📦 Processing {len(voters)} voters linearly...")
            
            for voter in voters:
                try:
                    full_address = self.create_full_address(voter)
                    
                    if not full_address.strip():
                        logger.warning(f"⚠️ Empty address for voter {voter['id']}")
                        total_processed += 1
                        continue
                    
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
🎉 POSTGRESQL LINEAR GEOCODING COMPLETE!
📊 Final Statistics:
   - Total Processed: {total_processed:,}
   - Successfully Geocoded: {total_geocoded:,}
   - Success Rate: {(total_geocoded/total_processed*100) if total_processed > 0 else 0:.1f}%
   - Total Time: {total_time/60:.1f} minutes
   - Average Rate: {total_geocoded/(total_time/60) if total_time > 0 else 0:.1f} geocodes/min
""")
        
        logger.info("🔄 Refreshing street-level summary data...")
        self.refresh_street_summary()
        
        return {
            'total_processed': total_processed,
            'total_geocoded': total_geocoded,
            'success_rate': (total_geocoded/total_processed*100) if total_processed > 0 else 0,
            'total_time_minutes': total_time/60,
            'geocodes_per_minute': total_geocoded/(total_time/60) if total_time > 0 else 0
        }
    
    def cleanup(self):
        """Clean up database connection."""
        if self.pg_conn:
            self.pg_conn.close()

def main():
    """Entry point for PostgreSQL linear geocoding."""
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not google_api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set!")
        logger.error("Please set your Google Maps API key:")
        logger.error("export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        return 1
    
    pg_config = {
        'pg_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'pg_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'pg_database': os.getenv('POSTGRES_DATABASE', 'voter_data'),
        'pg_user': os.getenv('POSTGRES_USER', 'postgres'),
        'pg_password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    logger.info("✅ Environment variables validated successfully")
    logger.info(f"📊 Google Maps API key: {google_api_key[:10]}... ({len(google_api_key)} chars)")
    logger.info(f"📊 PostgreSQL: {pg_config['pg_user']}@{pg_config['pg_host']}:{pg_config['pg_port']}/{pg_config['pg_database']}")
    
    geocoder = PostgresLinearGeocoder(google_api_key=google_api_key, **pg_config)
    
    try:
        if not geocoder.connect_postgres():
            logger.error("❌ Failed to connect to PostgreSQL")
            return 1
        
        if not geocoder.setup_google_maps():
            logger.error("❌ Failed to setup Google Maps client")
            return 1
        
        logger.info("🧪 Testing with small batch of 50 voters...")
        results = geocoder.run_linear_geocoding(max_voters=50)
        
        if results['total_geocoded'] > 0:
            logger.info("✅ Test successful! PostgreSQL linear geocoding is working.")
            logger.info("💡 To process more voters, increase max_voters parameter in run_linear_geocoding()")
        else:
            logger.warning("⚠️ No voters were geocoded. Check API key validity and data availability.")
        
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    finally:
        geocoder.cleanup()

if __name__ == "__main__":
    sys.exit(main())
