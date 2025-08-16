#!/usr/bin/env python3
"""
Create mapping visualizations showing individual voter locations by party affiliation.
"""

import os
import tempfile
import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoterMappingVisualizer:
    def __init__(self):
        self.project_id = "proj-roth"
        self.dataset_id = "voter_data"
        self.bq_client = None
        self.creds_file = None
        self.output_dir = "."
        
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
    
    def get_street_data(self) -> pd.DataFrame:
        """Get individual voter data from BigQuery instead of street-level aggregation."""
        
        voter_query = """
        SELECT 
            id,
            addr_residential_street_name as street_name,
            addr_residential_city as city,
            county_name as county,
            addr_residential_zip_code as zip_code,
            demo_party as party,
            latitude,
            longitude,
            geocoding_source,
            geocoding_accuracy
        FROM `@project_id.@dataset_id.voters`
        WHERE latitude IS NOT NULL 
          AND longitude IS NOT NULL
          AND demo_party IN ('REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED')
        ORDER BY RAND()
        LIMIT 5000
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", self.project_id),
                bigquery.ScalarQueryParameter("dataset_id", "STRING", self.dataset_id),
            ]
        )
        
        try:
            voter_df = self.bq_client.query(voter_query, job_config=job_config).to_dataframe()
            logger.info(f"Retrieved {len(voter_df)} individual voter records")
            
            if voter_df.empty:
                logger.warning("No voter data available for mapping")
                return None
                
            return voter_df
            
        except Exception as e:
            logger.error(f"Error querying voter data: {e}")
            return None
    
    def create_interactive_map(self, voter_df: pd.DataFrame) -> str:
        """Create an interactive map showing individual voter locations by party."""
        if voter_df is None or voter_df.empty:
            logger.warning("No data available for mapping")
            return None
        
        nj_center = [40.0583, -74.4057]
        m = folium.Map(location=nj_center, zoom_start=8)
        
        party_colors = {
            'REPUBLICAN': 'red',
            'DEMOCRAT': 'blue', 
            'UNAFFILIATED': 'gray'
        }
        
        sample_size = min(2000, len(voter_df))
        sampled_df = voter_df.sample(n=sample_size) if len(voter_df) > sample_size else voter_df
        
        for _, row in sampled_df.iterrows():
            color = party_colors.get(row['party'], 'gray')
            
            popup_text = f"""
            <b>Voter ID:</b> {row['id']}<br>
            <b>Party:</b> {row['party']}<br>
            <b>Address:</b> {row['street_name']}<br>
            {row['city']}, {row['county']} County<br>
            <b>Zip:</b> {row['zip_code']}<br>
            <b>Geocoding:</b> {row['geocoding_source']} ({row['geocoding_accuracy']})
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fillColor=color,
                fillOpacity=0.6,
                weight=1
            ).add_to(m)
        
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 110px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Individual Voters</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Republican</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Democrat</p>
        <p><i class="fa fa-circle" style="color:gray"></i> Unaffiliated</p>
        <p><small>Showing {sample_size:,} voters</small></p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def create_county_summary(self, voter_df: pd.DataFrame) -> go.Figure:
        """Create county-level summary charts from individual voter data."""
        if voter_df is None or voter_df.empty:
            return None
        
        county_summary = voter_df.groupby(['county', 'party']).size().unstack(fill_value=0).reset_index()
        
        county_summary['total_voters'] = county_summary.sum(axis=1, numeric_only=True)
        
        for party in ['REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED']:
            if party in county_summary.columns:
                county_summary[f'{party.lower()}_pct'] = (county_summary[party] / county_summary['total_voters'] * 100).round(1)
            else:
                county_summary[f'{party.lower()}_pct'] = 0
        
        county_summary = county_summary.sort_values('total_voters', ascending=True)
        
        fig = go.Figure()
        
        if 'REPUBLICAN' in county_summary.columns:
            fig.add_trace(go.Bar(
                name='Republican',
                y=county_summary['county'],
                x=county_summary['republican_pct'],
                orientation='h',
                marker_color='red',
                text=county_summary['republican_pct'].astype(str) + '%',
                textposition='inside'
            ))
        
        if 'DEMOCRAT' in county_summary.columns:
            fig.add_trace(go.Bar(
                name='Democrat', 
                y=county_summary['county'],
                x=county_summary['democrat_pct'],
                orientation='h',
                marker_color='blue',
                text=county_summary['democrat_pct'].astype(str) + '%',
                textposition='inside'
            ))
        
        if 'UNAFFILIATED' in county_summary.columns:
            fig.add_trace(go.Bar(
                name='Unaffiliated',
                y=county_summary['county'], 
                x=county_summary['unaffiliated_pct'],
                orientation='h',
                marker_color='gray',
                text=county_summary['unaffiliated_pct'].astype(str) + '%',
                textposition='inside'
            ))
        
        fig.update_layout(
            title='Political Party Distribution by County (Individual Voter Data)',
            xaxis_title='Percentage of Voters',
            yaxis_title='County',
            barmode='stack',
            height=600,
            showlegend=True
        )
        
        return fig
    
    def analyze_geographic_patterns(self, voter_df: pd.DataFrame) -> Dict:
        """Analyze geographic patterns in the individual voter data."""
        if voter_df is None or voter_df.empty:
            return {}
        
        try:
            analysis = {
                'total_counties': len(voter_df['county'].unique()),
                'total_cities': len(voter_df['city'].unique()),
                'party_distribution': voter_df['party'].value_counts().to_dict(),
                'geocoding_sources': voter_df['geocoding_source'].value_counts().to_dict(),
                'accuracy_distribution': voter_df['geocoding_accuracy'].value_counts().to_dict()
            }
            
            city_party_counts = voter_df.groupby(['city', 'county', 'party']).size().reset_index(name='voter_count')
            
            republican_cities = city_party_counts[city_party_counts['party'] == 'REPUBLICAN'].nlargest(5, 'voter_count')
            democrat_cities = city_party_counts[city_party_counts['party'] == 'DEMOCRAT'].nlargest(5, 'voter_count')
            
            analysis['top_republican_cities'] = republican_cities[['city', 'county', 'voter_count']].to_dict('records')
            analysis['top_democrat_cities'] = democrat_cities[['city', 'county', 'voter_count']].to_dict('records')
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing geographic patterns: {e}")
            return {}
    
    def create_summary_report(self, voter_df: pd.DataFrame, geo_analysis: Dict) -> Dict:
        """Create a summary report of the mapping analysis from individual voter data."""
        if voter_df is None or voter_df.empty:
            return {}
        
        try:
            party_counts = voter_df['party'].value_counts()
            
            summary = {
                'data_summary': {
                    'total_voters_mapped': len(voter_df),
                    'counties_covered': len(voter_df['county'].unique()),
                    'cities_covered': len(voter_df['city'].unique()),
                    'unique_streets': len(voter_df['street_name'].unique())
                },
                'party_breakdown': {
                    'total_republican': int(party_counts.get('REPUBLICAN', 0)),
                    'total_democrat': int(party_counts.get('DEMOCRAT', 0)),
                    'total_unaffiliated': int(party_counts.get('UNAFFILIATED', 0))
                },
                'geographic_analysis': geo_analysis,
                'top_counties_by_voters': voter_df['county'].value_counts().head(5).to_dict(),
                'geocoding_quality': {
                    'google_maps': int(voter_df[voter_df['geocoding_source'] == 'GOOGLE_MAPS'].shape[0]),
                    'us_census': int(voter_df[voter_df['geocoding_source'] == 'US_CENSUS'].shape[0])
                }
            }
            
            total_mapped = summary['data_summary']['total_voters_mapped']
            if total_mapped > 0:
                summary['party_percentages'] = {
                    'republican_pct': round(summary['party_breakdown']['total_republican'] / total_mapped * 100, 2),
                    'democrat_pct': round(summary['party_breakdown']['total_democrat'] / total_mapped * 100, 2),
                    'unaffiliated_pct': round(summary['party_breakdown']['total_unaffiliated'] / total_mapped * 100, 2)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
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
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
            return False
        finally:
            self.cleanup_credentials()

def main():
    visualizer = VoterMappingVisualizer()
    
    if not visualizer.generate_all_visualizations():
        print("❌ Failed to generate visualizations. Check logs for details.")
        return False
    
    try:
        query = """
        SELECT 
            COUNT(*) as total_voters,
            COUNT(latitude) as geocoded_voters,
            ROUND(COUNT(latitude) * 100.0 / COUNT(*), 2) as geocoded_percentage
        FROM `@project_id.@dataset_id.voters`
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", "proj-roth"),
                bigquery.ScalarQueryParameter("dataset_id", "STRING", "voter_data"),
            ]
        )
        
        result = visualizer.bq_client.query(query, job_config=job_config).to_dataframe()
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
        print("  - voter_map.html (Interactive individual voter map)")
        print("  - county_summary.html (County summary charts)")
        print("\nOpen these HTML files in your browser to view the interactive visualizations!")
    else:
        print("❌ Failed to generate visualizations")
    
    return success

if __name__ == "__main__":
    main()
