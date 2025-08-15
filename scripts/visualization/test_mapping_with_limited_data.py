#!/usr/bin/env python3
"""
Test mapping visualizations with the limited geocoded data available.
"""

import os
import tempfile
from google.cloud import bigquery
from create_mapping_visualizations import VoterMappingVisualizer

def main():
    credentials_json = os.getenv('GCP_CREDENTIALS')
    if not credentials_json:
        print("No GCP_CREDENTIALS found")
        return False
    
    print("🗺️  Testing mapping visualizations with limited geocoded data...")
    
    visualizer = VoterMappingVisualizer()
    
    if visualizer.setup_credentials():
        try:
            voter_df = visualizer.get_geocoded_voter_sample(limit=1000)
            print(f"Retrieved {len(voter_df)} geocoded voters for testing")
            
            if not voter_df.empty:
                print("Testing Folium map generation...")
                map_file = visualizer.create_folium_map(voter_df, "test_voter_map.html")
                if map_file:
                    print(f"✅ Successfully created test map: {map_file}")
                
                print("Testing county summary chart...")
                county_file = visualizer.create_county_summary_chart(voter_df, "test_county_summary.html")
                if county_file:
                    print(f"✅ Successfully created county summary: {county_file}")
                
                print("🎉 Mapping visualization framework is working!")
                return True
            else:
                print("❌ No geocoded data available for testing")
                return False
                
        except Exception as e:
            print(f"❌ Error testing visualizations: {e}")
            return False
        finally:
            visualizer.cleanup_credentials()
    else:
        print("❌ Failed to setup credentials")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Test result: {'PASSED' if success else 'FAILED'}")
