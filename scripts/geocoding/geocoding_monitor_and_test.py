#!/usr/bin/env python3
"""
Comprehensive geocoding monitoring and mapping test script.
Monitors geocoding progress and generates sample visualizations when sufficient data is available.
"""

import os
import tempfile
import time
from datetime import datetime
from google.cloud import bigquery
from create_mapping_visualizations import VoterMappingVisualizer

class GeocodingMonitor:
    def __init__(self):
        self.project_id = 'proj-roth'
        self.dataset_id = 'voter_data'
        self.client = None
        self.visualizer = None
        
    def setup_credentials(self):
        """Setup BigQuery credentials from environment variable."""
        credentials_json = os.getenv('GCP_CREDENTIALS')
        if not credentials_json:
            print("❌ No GCP_CREDENTIALS environment variable found")
            return False
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(credentials_json)
                self.creds_file = f.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_file
            self.client = bigquery.Client(project=self.project_id)
            self.visualizer = VoterMappingVisualizer()
            return True
        except Exception as e:
            print(f"❌ Error setting up credentials: {e}")
            return False
    
    def get_geocoding_stats(self):
        """Get current geocoding statistics."""
        try:
            query = '''
            SELECT 
                COUNT(*) as total_voters,
                COUNT(latitude) as geocoded_voters,
                ROUND(COUNT(latitude) * 100.0 / COUNT(*), 2) as geocoded_percentage,
                COUNT(DISTINCT county_name) as counties_with_data
            FROM `proj-roth.voter_data.voters`
            '''
            
            result = self.client.query(query).to_dataframe()
            return {
                'total_voters': int(result.iloc[0]['total_voters']),
                'geocoded_voters': int(result.iloc[0]['geocoded_voters']),
                'geocoded_percentage': float(result.iloc[0]['geocoded_percentage']),
                'counties_with_data': int(result.iloc[0]['counties_with_data'])
            }
        except Exception as e:
            print(f"❌ Error getting geocoding stats: {e}")
            return None
    
    def get_county_breakdown(self):
        """Get geocoding progress by county."""
        try:
            query = '''
            SELECT 
                county_name,
                COUNT(*) as total_voters,
                COUNT(latitude) as geocoded_voters,
                ROUND(COUNT(latitude) * 100.0 / COUNT(*), 1) as geocoded_percentage
            FROM `proj-roth.voter_data.voters`
            GROUP BY county_name
            ORDER BY geocoded_voters DESC
            LIMIT 10
            '''
            
            return self.client.query(query).to_dataframe()
        except Exception as e:
            print(f"❌ Error getting county breakdown: {e}")
            return None
    
    def get_party_distribution_sample(self, limit=100):
        """Get sample of geocoded voters by party affiliation."""
        try:
            query = f'''
            SELECT 
                demo_party,
                COUNT(*) as count,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lng
            FROM `proj-roth.voter_data.voters`
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY demo_party
            ORDER BY count DESC
            '''
            
            return self.client.query(query).to_dataframe()
        except Exception as e:
            print(f"❌ Error getting party distribution: {e}")
            return None
    
    def test_mapping_framework(self, min_records=50):
        """Test mapping visualization framework if sufficient data is available."""
        stats = self.get_geocoding_stats()
        if not stats or stats['geocoded_voters'] < min_records:
            print(f"⏳ Not enough geocoded data yet ({stats['geocoded_voters'] if stats else 0} < {min_records})")
            return False
        
        try:
            print(f"🗺️  Testing mapping framework with {stats['geocoded_voters']} geocoded voters...")
            
            if not self.visualizer.setup_credentials():
                print("❌ Failed to setup visualizer credentials")
                return False
            
            voter_df = self.visualizer.get_geocoded_voter_sample(limit=min(1000, stats['geocoded_voters']))
            
            if not voter_df.empty:
                print(f"✅ Retrieved {len(voter_df)} voters for testing")
                
                map_file = self.visualizer.create_folium_map(voter_df, "test_voter_map.html")
                if map_file:
                    print(f"✅ Successfully created test map: {map_file}")
                
                county_file = self.visualizer.create_county_summary_chart(voter_df, "test_county_summary.html")
                if county_file:
                    print(f"✅ Successfully created county summary: {county_file}")
                
                return True
            else:
                print("❌ No geocoded data retrieved")
                return False
                
        except Exception as e:
            print(f"❌ Error testing mapping framework: {e}")
            return False
    
    def print_progress_report(self):
        """Print comprehensive progress report."""
        print("\n" + "="*60)
        print(f"🗺️  GEOCODING PROGRESS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        stats = self.get_geocoding_stats()
        if stats:
            print(f"📊 Total voters: {stats['total_voters']:,}")
            print(f"📍 Geocoded voters: {stats['geocoded_voters']:,}")
            print(f"📈 Progress: {stats['geocoded_percentage']}%")
            print(f"🏛️  Counties with data: {stats['counties_with_data']}")
            
            if stats['geocoded_percentage'] > 0:
                remaining_voters = stats['total_voters'] - stats['geocoded_voters']
                estimated_hours = (remaining_voters / stats['geocoded_voters']) * 0.5  # Assuming ~30min for current progress
                print(f"⏱️  Estimated completion: ~{estimated_hours:.1f} hours")
        
        print("\n📍 Top Counties by Geocoded Voters:")
        county_df = self.get_county_breakdown()
        if county_df is not None and not county_df.empty:
            for _, row in county_df.head(5).iterrows():
                print(f"  {row['county_name']}: {row['geocoded_voters']:,} / {row['total_voters']:,} ({row['geocoded_percentage']}%)")
        
        print("\n🎯 Party Distribution (Geocoded Sample):")
        party_df = self.get_party_distribution_sample()
        if party_df is not None and not party_df.empty:
            for _, row in party_df.head(5).iterrows():
                print(f"  {row['demo_party']}: {row['count']:,} voters")
        
        print("="*60)
        return stats
    
    def cleanup(self):
        """Clean up temporary files."""
        if hasattr(self, 'creds_file') and os.path.exists(self.creds_file):
            os.unlink(self.creds_file)
        if self.visualizer:
            self.visualizer.cleanup_credentials()

def main():
    monitor = GeocodingMonitor()
    
    if not monitor.setup_credentials():
        return False
    
    try:
        stats = monitor.print_progress_report()
        
        if stats and stats['geocoded_voters'] >= 50:
            print(f"\n🧪 Testing mapping visualization framework...")
            success = monitor.test_mapping_framework()
            if success:
                print("🎉 Mapping framework test completed successfully!")
            else:
                print("⚠️  Mapping framework test encountered issues")
        else:
            print(f"\n⏳ Waiting for more geocoded data before testing mapping framework...")
            print(f"   Current: {stats['geocoded_voters'] if stats else 0} | Minimum needed: 50")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in monitoring: {e}")
        return False
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
