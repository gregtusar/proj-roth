#!/usr/bin/env python3
"""
Fixed mapping visualization script with proper GCP authentication.
Generates interactive maps and charts for individual voter records by party affiliation.
"""

import os
import sys
import logging
import tempfile
import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoterMappingVisualizer:
    """Generate mapping visualizations for individual voter data."""
    
    def __init__(self):
        self.project_id = "proj-roth"
        self.dataset_id = "voter_data"
        self.bq_client = None
        self.creds_file = None
        self.output_dir = "."
    
    def setup_credentials(self):
        """Set up GCP credentials from environment variable."""
        try:
            creds_json = os.getenv('GCP_CREDENTIALS')
            if not creds_json:
                logger.error("GCP_CREDENTIALS environment variable not set")
                return False
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(creds_json)
                self.creds_file = f.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_file
            self.bq_client = bigquery.Client(project=self.project_id)
            logger.info("✅ Successfully set up GCP credentials")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set up credentials: {e}")
            return False
    
    def cleanup_credentials(self):
        """Clean up temporary credentials file."""
        if self.creds_file and os.path.exists(self.creds_file):
            try:
                os.unlink(self.creds_file)
                logger.info("🧹 Cleaned up temporary credentials file")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean up credentials file: {e}")
    
    def get_voter_data(self, limit=10000):
        """Retrieve individual voter data from BigQuery."""
        try:
            query = f"""
            SELECT 
                id,
                first_name,
                last_name,
                party,
                county,
                municipality,
                latitude,
                longitude,
                geocoding_source,
                geocoding_accuracy
            FROM `{self.project_id}.{self.dataset_id}.voters`
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            LIMIT @limit
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )
            
            logger.info(f"🔍 Querying voter data (limit: {limit:,})")
            df = self.bq_client.query(query, job_config=job_config).to_dataframe()
            
            if df.empty:
                logger.warning("No geocoded voter data found")
                return None
            
            logger.info(f"✅ Retrieved {len(df):,} geocoded voters")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error querying voter data: {e}")
            return None
    
    def create_interactive_map(self, voter_df):
        """Create interactive map with individual voter locations."""
        if voter_df is None or voter_df.empty:
            logger.error("No voter data available for mapping")
            return None
        
        try:
            nj_center = [40.0583, -74.4057]
            m = folium.Map(location=nj_center, zoom_start=8, tiles='OpenStreetMap')
            
            party_colors = {
                'DEM': 'blue',
                'REP': 'red', 
                'UNA': 'gray',
                'GRE': 'green',
                'LIB': 'yellow',
                'IND': 'purple'
            }
            
            for _, voter in voter_df.iterrows():
                color = party_colors.get(voter.get('party', 'UNA'), 'gray')
                
                popup_text = f"""
                <b>{voter.get('first_name', '')} {voter.get('last_name', '')}</b><br>
                Party: {voter.get('party', 'Unknown')}<br>
                County: {voter.get('county', 'Unknown')}<br>
                Municipality: {voter.get('municipality', 'Unknown')}<br>
                Source: {voter.get('geocoding_source', 'Unknown')}
                """
                
                folium.CircleMarker(
                    location=[voter['latitude'], voter['longitude']],
                    radius=3,
                    popup=folium.Popup(popup_text, max_width=300),
                    color=color,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=1
                ).add_to(m)
            
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 150px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>Party Affiliation</b></p>
            <p><i class="fa fa-circle" style="color:blue"></i> Democrat</p>
            <p><i class="fa fa-circle" style="color:red"></i> Republican</p>
            <p><i class="fa fa-circle" style="color:gray"></i> Unaffiliated</p>
            <p><i class="fa fa-circle" style="color:green"></i> Green</p>
            <p><i class="fa fa-circle" style="color:yellow"></i> Libertarian</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            logger.info(f"✅ Created interactive map with {len(voter_df):,} voters")
            return m
            
        except Exception as e:
            logger.error(f"❌ Error creating interactive map: {e}")
            return None
    
    def create_county_summary(self, voter_df):
        """Create county-level summary charts."""
        if voter_df is None or voter_df.empty:
            logger.error("No voter data available for county summary")
            return None
        
        try:
            county_party = voter_df.groupby(['county', 'party']).size().reset_index(name='count')
            county_totals = voter_df.groupby('county').size().reset_index(name='total')
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Party Distribution by County', 'Total Voters by County'),
                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            )
            
            party_colors = {
                'DEM': 'blue',
                'REP': 'red',
                'UNA': 'lightgray',
                'GRE': 'green',
                'LIB': 'gold',
                'IND': 'purple'
            }
            
            for party in county_party['party'].unique():
                party_data = county_party[county_party['party'] == party]
                fig.add_trace(
                    go.Bar(
                        x=party_data['county'],
                        y=party_data['count'],
                        name=party,
                        marker_color=party_colors.get(party, 'gray')
                    ),
                    row=1, col=1
                )
            
            fig.add_trace(
                go.Bar(
                    x=county_totals['county'],
                    y=county_totals['total'],
                    name='Total Voters',
                    marker_color='steelblue',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=800,
                title_text=f"New Jersey Voter Analysis - {len(voter_df):,} Geocoded Voters",
                showlegend=True
            )
            
            fig.update_xaxes(title_text="County", row=2, col=1)
            fig.update_yaxes(title_text="Number of Voters", row=1, col=1)
            fig.update_yaxes(title_text="Total Voters", row=2, col=1)
            
            logger.info("✅ Created county summary charts")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Error creating county summary: {e}")
            return None
    
    def analyze_geographic_patterns(self, voter_df):
        """Analyze geographic patterns in voter data."""
        if voter_df is None or voter_df.empty:
            return {}
        
        try:
            analysis = {
                'total_voters': len(voter_df),
                'counties': voter_df['county'].nunique(),
                'municipalities': voter_df['municipality'].nunique(),
                'party_breakdown': voter_df['party'].value_counts().to_dict(),
                'geocoding_sources': voter_df['geocoding_source'].value_counts().to_dict(),
                'top_counties': voter_df['county'].value_counts().head(5).to_dict()
            }
            
            logger.info("✅ Completed geographic pattern analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in geographic analysis: {e}")
            return {}
    
    def create_summary_report(self, voter_df, geo_analysis):
        """Create a summary report of the analysis."""
        if not geo_analysis:
            return {}
        
        try:
            report = {
                'summary': f"Analyzed {geo_analysis.get('total_voters', 0):,} geocoded voters across {geo_analysis.get('counties', 0)} counties",
                'party_distribution': geo_analysis.get('party_breakdown', {}),
                'geographic_coverage': {
                    'counties': geo_analysis.get('counties', 0),
                    'municipalities': geo_analysis.get('municipalities', 0)
                },
                'data_quality': {
                    'geocoding_sources': geo_analysis.get('geocoding_sources', {}),
                    'completion_rate': f"{(geo_analysis.get('total_voters', 0) / 622304 * 100):.2f}%" if geo_analysis.get('total_voters') else "0%"
                }
            }
            
            logger.info("✅ Created summary report")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error creating summary report: {e}")
            return {}
    
    def generate_all_visualizations(self):
        """Generate all mapping visualizations using individual voter data."""
        if not self.setup_credentials():
            logger.error("❌ Failed to set up credentials. Make sure GCP_CREDENTIALS environment variable is set.")
            return False
        
        try:
            logger.info("🗺️  Starting BigQuery mapping visualization generation...")
            
            voter_df = self.get_voter_data(limit=10000)
            if voter_df is None or voter_df.empty:
                logger.error("No voter data available - cannot generate visualizations")
                return False
            
            logger.info("📍 Creating interactive voter map...")
            map_obj = self.create_interactive_map(voter_df)
            if map_obj:
                map_path = os.path.join(self.output_dir, 'voter_map.html')
                map_obj.save(map_path)
                logger.info(f"✅ Interactive map saved to {map_path}")
            
            logger.info("📊 Creating county summary charts...")
            county_fig = self.create_county_summary(voter_df)
            if county_fig:
                county_path = os.path.join(self.output_dir, 'county_summary.html')
                county_fig.write_html(county_path)
                logger.info(f"✅ County summary saved to {county_path}")
            
            logger.info("🌍 Generating geographic analysis...")
            geo_analysis = self.analyze_geographic_patterns(voter_df)
            
            logger.info("📋 Creating summary report...")
            summary = self.create_summary_report(voter_df, geo_analysis)
            
            logger.info("✅ All visualizations generated successfully!")
            logger.info(f"📊 Summary: {summary.get('summary', 'No summary available')}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
            return False
        finally:
            self.cleanup_credentials()

def main():
    """Main function to run the visualization generator."""
    visualizer = VoterMappingVisualizer()
    
    result = visualizer.generate_all_visualizations()
    if not result:
        print("❌ Failed to generate visualizations. Check logs for details.")
        return False
    
    print("✅ Visualizations generated successfully!")
    print(f"📊 {result.get('summary', 'Analysis complete')}")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
