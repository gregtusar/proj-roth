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
            voter_id,
            first_name,
            last_name,
            party_affiliation,
            county,
            municipality,
            street_address,
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
        """Get street-level party summary data."""
        query = f"""
        SELECT 
            street_address,
            county,
            municipality,
            latitude,
            longitude,
            total_voters,
            republican_count,
            democratic_count,
            unaffiliated_count,
            other_count,
            ROUND(republican_count * 100.0 / total_voters, 1) as republican_pct,
            ROUND(democratic_count * 100.0 / total_voters, 1) as democratic_pct
        FROM `{self.project_id}.{self.dataset_id}.street_party_summary`
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND total_voters >= 5  -- Only streets with meaningful voter counts
        ORDER BY total_voters DESC
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} street-level summaries")
            return df
        except Exception as e:
            logger.error(f"Error retrieving street party summary: {e}")
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
                
            color = party_colors.get(row['party_affiliation'], 'gray')
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=f"{row['first_name']} {row['last_name']}<br>"
                      f"Party: {row['party_affiliation']}<br>"
                      f"Address: {row['street_address']}<br>"
                      f"County: {row['county']}",
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
        """Create a heatmap showing party concentrations by street."""
        if street_df.empty:
            logger.warning("No street data available for heatmap")
            return None
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Republican Concentration', 'Democratic Concentration'),
            specs=[[{"type": "scattermapbox"}, {"type": "scattermapbox"}]]
        )
        
        fig.add_trace(
            go.Scattermapbox(
                lat=street_df['latitude'],
                lon=street_df['longitude'],
                mode='markers',
                marker=dict(
                    size=street_df['total_voters'] / 2,
                    color=street_df['republican_pct'],
                    colorscale='Reds',
                    cmin=0,
                    cmax=100,
                    colorbar=dict(title="Republican %", x=0.45)
                ),
                text=street_df.apply(lambda x: 
                    f"Street: {x['street_address']}<br>"
                    f"County: {x['county']}<br>"
                    f"Total Voters: {x['total_voters']}<br>"
                    f"Republican: {x['republican_pct']}%", axis=1),
                hovertemplate='%{text}<extra></extra>',
                name='Republican %'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scattermapbox(
                lat=street_df['latitude'],
                lon=street_df['longitude'],
                mode='markers',
                marker=dict(
                    size=street_df['total_voters'] / 2,
                    color=street_df['democratic_pct'],
                    colorscale='Blues',
                    cmin=0,
                    cmax=100,
                    colorbar=dict(title="Democratic %", x=1.02)
                ),
                text=street_df.apply(lambda x: 
                    f"Street: {x['street_address']}<br>"
                    f"County: {x['county']}<br>"
                    f"Total Voters: {x['total_voters']}<br>"
                    f"Democratic: {x['democratic_pct']}%", axis=1),
                hovertemplate='%{text}<extra></extra>',
                name='Democratic %'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="Street-Level Political Concentrations in New Jersey",
            height=600,
            mapbox1=dict(
                style="open-street-map",
                center=dict(lat=40.0583, lon=-74.4057),
                zoom=8
            ),
            mapbox2=dict(
                style="open-street-map", 
                center=dict(lat=40.0583, lon=-74.4057),
                zoom=8
            ),
            showlegend=False
        )
        
        fig.write_html(output_file)
        logger.info(f"Saved heatmap visualization to {output_file}")
        return output_file
    
    def create_county_summary_chart(self, df, output_file="county_summary.html"):
        """Create county-level summary charts."""
        if df.empty:
            logger.warning("No data available for county summary")
            return None
        
        county_summary = df.groupby('county').agg({
            'party_affiliation': 'count',
            'latitude': 'first',
            'longitude': 'first'
        }).rename(columns={'party_affiliation': 'total_voters'}).reset_index()
        
        party_by_county = df.groupby(['county', 'party_affiliation']).size().unstack(fill_value=0)
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
                self.create_folium_map(voter_df, "voter_distribution_map.html")
                self.create_county_summary_chart(voter_df, "county_party_breakdown.html")
            
            street_df = self.get_street_party_summary()
            if not street_df.empty:
                self.create_heatmap_visualization(street_df, "street_level_heatmap.html")
            
            logger.info("✅ All visualizations generated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
            return False
        finally:
            self.cleanup_credentials()

def main():
    visualizer = VoterMappingVisualizer()
    success = visualizer.generate_all_visualizations()
    
    if success:
        print("🎉 Mapping visualizations created successfully!")
        print("Generated files:")
        print("  - voter_distribution_map.html (Interactive voter map)")
        print("  - street_level_heatmap.html (Street-level party heatmap)")
        print("  - county_party_breakdown.html (County summary charts)")
    else:
        print("❌ Failed to generate visualizations")
    
    return success

if __name__ == "__main__":
    main()
