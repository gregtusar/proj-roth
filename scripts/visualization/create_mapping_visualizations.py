#!/usr/bin/env python3
"""
Create mapping visualizations showing political concentrations by street level.
"""

import os
import tempfile
import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoterMappingVisualizer:
    def __init__(self):
        self.project_id = "proj-roth"
        self.dataset_id = "voter_data"
        self.bq_client = None
        self.creds_file = None
        
    def setup_credentials(self):
        """Set up GCP credentials from environment variable."""
        credentials_json = os.getenv('GCP_CREDENTIALS')
        if not credentials_json:
            logger.error("No GCP_CREDENTIALS found")
            return False
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(credentials_json)
                self.creds_file = f.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_file
            self.bq_client = bigquery.Client(project=self.project_id)
            logger.info("✅ Successfully set up GCP credentials")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up credentials: {e}")
            return False
    
    def cleanup_credentials(self):
        """Clean up temporary credentials file."""
        if self.creds_file and os.path.exists(self.creds_file):
            try:
                os.unlink(self.creds_file)
            except:
                pass
    
    def get_geocoded_voter_sample(self, limit=10000):
        """Get a sample of geocoded voters for visualization."""
        query = f"""
        SELECT 
            id,
            name_first,
            name_last,
            demo_party,
            county_name,
            addr_residential_city,
            addr_residential_line1,
            latitude,
            longitude,
            geocoding_source,
            geocoding_accuracy
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND latitude BETWEEN 38.0 AND 42.0  -- NJ bounds
        AND longitude BETWEEN -76.0 AND -73.0  -- NJ bounds
        ORDER BY RAND()
        LIMIT {limit}
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} geocoded voters for visualization")
            return df
        except Exception as e:
            logger.error(f"Error retrieving geocoded voters: {e}")
            return pd.DataFrame()
    
    def get_street_party_summary(self):
        """DEPRECATED: Street-level aggregation removed per user request."""
        logger.warning("Street-level aggregation has been removed - using individual voter records only")
        return pd.DataFrame()
    
    def create_folium_map(self, df, output_file="voter_map.html"):
        """Create an interactive Folium map showing voter concentrations."""
        if df.empty:
            logger.warning("No data available for mapping")
            return None
        
        nj_center = [40.0583, -74.4057]
        m = folium.Map(location=nj_center, zoom_start=8)
        
        party_colors = {
            'REP': 'red',
            'DEM': 'blue', 
            'UNA': 'gray',
            'GRE': 'green',
            'LIB': 'orange'
        }
        
        for idx, row in df.iterrows():
            if idx > 5000:  # Limit markers for performance
                break
                
            color = party_colors.get(row['demo_party'], 'gray')
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=f"{row['name_first']} {row['name_last']}<br>"
                      f"Party: {row['demo_party']}<br>"
                      f"Address: {row['addr_residential_line1']}<br>"
                      f"County: {row['county_name']}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6
            ).add_to(m)
        
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Party Affiliation</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Republican</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Democrat</p>
        <p><i class="fa fa-circle" style="color:gray"></i> Unaffiliated</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        m.save(output_file)
        logger.info(f"Saved interactive map to {output_file}")
        return output_file
    
    def create_heatmap_visualization(self, street_df, output_file="party_heatmap.html"):
        """DEPRECATED: Street-level heatmap removed per user request."""
        logger.warning("Street-level heatmap visualization has been removed - using individual voter maps only")
        return None
    
    def create_county_summary_chart(self, df, output_file="county_summary.html"):
        """Create county-level summary charts."""
        if df.empty:
            logger.warning("No data available for county summary")
            return None
        
        county_summary = df.groupby('county_name').agg({
            'demo_party': 'count',
            'latitude': 'first',
            'longitude': 'first'
        }).rename(columns={'demo_party': 'total_voters'}).reset_index()
        
        party_by_county = df.groupby(['county_name', 'demo_party']).size().unstack(fill_value=0)
        party_by_county = party_by_county.div(party_by_county.sum(axis=1), axis=0) * 100
        
        fig = go.Figure()
        
        colors = {'REP': 'red', 'DEM': 'blue', 'UNA': 'gray', 'GRE': 'green', 'LIB': 'orange'}
        
        for party in party_by_county.columns:
            if party in colors:
                fig.add_trace(go.Bar(
                    name=party,
                    x=party_by_county.index,
                    y=party_by_county[party],
                    marker_color=colors[party]
                ))
        
        fig.update_layout(
            title="Party Affiliation by County (%)",
            xaxis_title="County",
            yaxis_title="Percentage",
            barmode='stack',
            height=500
        )
        
        fig.write_html(output_file)
        logger.info(f"Saved county summary to {output_file}")
        return output_file
    
    def generate_all_visualizations(self):
        """Generate all mapping visualizations."""
        if not self.setup_credentials():
            return False
        
        try:
            logger.info("🗺️  Generating mapping visualizations...")
            
            voter_df = self.get_geocoded_voter_sample(limit=10000)
            if not voter_df.empty:
                logger.info(f"Creating visualizations with {len(voter_df)} geocoded voters")
                self.create_folium_map(voter_df, "voter_distribution_map.html")
                self.create_county_summary_chart(voter_df, "county_party_breakdown.html")
                
                if len(voter_df) >= 100:  # Only create individual voter visualizations
                    logger.info("Creating individual voter-based visualizations only")
                else:
                    logger.info(f"Skipping advanced visualizations - need at least 100 geocoded voters (have {len(voter_df)})")
            else:
                logger.warning("No geocoded voter data available for visualization")
                return False
            
            logger.info("✅ All visualizations generated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
            return False
        finally:
            self.cleanup_credentials()

def main():
    visualizer = VoterMappingVisualizer()
    
    if visualizer.setup_credentials():
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_voters,
                COUNT(latitude) as geocoded_voters,
                ROUND(COUNT(latitude) * 100.0 / COUNT(*), 2) as geocoded_percentage
            FROM `proj-roth.voter_data.voters`
            """
            
            result = visualizer.bq_client.query(query).to_dataframe()
            total = int(result.iloc[0]['total_voters'])
            geocoded = int(result.iloc[0]['geocoded_voters'])
            percentage = float(result.iloc[0]['geocoded_percentage'])
            
            print(f"📊 Current geocoding progress: {geocoded:,} / {total:,} ({percentage}%)")
            
            if geocoded < 50:
                print(f"⚠️  Warning: Only {geocoded} voters are geocoded. Visualizations will be limited.")
                print("   Consider waiting for more geocoding progress for better results.")
            
        except Exception as e:
            print(f"❌ Error checking progress: {e}")
        finally:
            visualizer.cleanup_credentials()
    
    success = visualizer.generate_all_visualizations()
    
    if success:
        print("\n🎉 Mapping visualizations created successfully!")
        print("Generated files:")
        print("  - voter_distribution_map.html (Interactive individual voter map)")
        print("  - county_party_breakdown.html (County summary charts)")
        print("\nOpen these HTML files in your browser to view the interactive visualizations!")
    else:
        print("❌ Failed to generate visualizations")
    
    return success

if __name__ == "__main__":
    main()
