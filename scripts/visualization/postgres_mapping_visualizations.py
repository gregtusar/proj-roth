#!/usr/bin/env python3
"""
PostgreSQL-based mapping visualization script to replace BigQuery dependencies.
Creates interactive voter maps and county summaries using PostgreSQL data.
"""

import os
import sys
import logging
import pandas as pd
import psycopg2
import folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgresMappingVisualizations:
    """Creates voter mapping visualizations using PostgreSQL data."""
    
    def __init__(self, 
                 pg_host: str = 'localhost',
                 pg_port: int = 5432,
                 pg_database: str = 'voter_data',
                 pg_user: str = 'postgres',
                 pg_password: str = None):
        
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_database = pg_database
        self.pg_user = pg_user
        self.pg_password = pg_password or os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        self.pg_conn = None
        
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password
            )
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to PostgreSQL: {e}")
            return False
    
    def get_voter_data(self, limit: int = 10000) -> pd.DataFrame:
        """Get voter data with geocoding information from PostgreSQL."""
        query = """
        SELECT 
            id,
            name_first,
            name_last,
            addr_residential_line1,
            addr_residential_city,
            county_name,
            demo_party,
            latitude,
            longitude,
            geocoding_accuracy
        FROM voters
        WHERE latitude IS NOT NULL 
          AND longitude IS NOT NULL
          AND demo_party IS NOT NULL
        ORDER BY RANDOM()
        LIMIT %s
        """
        
        try:
            df = pd.read_sql_query(query, self.pg_conn, params=[limit])
            logger.info(f"Retrieved {len(df)} voters with geocoding data")
            return df
        except Exception as e:
            logger.error(f"Error retrieving voter data: {e}")
            return pd.DataFrame()
    
    def get_street_data(self) -> pd.DataFrame:
        """Get street-level party summary data from PostgreSQL."""
        query = """
        SELECT 
            street_name,
            city,
            county,
            republican_count,
            democrat_count,
            unaffiliated_count,
            other_party_count,
            total_voters,
            republican_pct,
            democrat_pct,
            unaffiliated_pct,
            street_center_latitude,
            street_center_longitude
        FROM street_party_summary
        WHERE total_voters >= 5
        ORDER BY total_voters DESC
        """
        
        try:
            df = pd.read_sql_query(query, self.pg_conn)
            logger.info(f"Retrieved {len(df)} street summaries")
            return df
        except Exception as e:
            logger.error(f"Error retrieving street data: {e}")
            return pd.DataFrame()
    
    def get_county_summary(self) -> pd.DataFrame:
        """Get county-level voter statistics from PostgreSQL."""
        query = """
        SELECT 
            county_name,
            demo_party,
            COUNT(*) as voter_count,
            AVG(latitude) as center_lat,
            AVG(longitude) as center_lng
        FROM voters
        WHERE latitude IS NOT NULL 
          AND longitude IS NOT NULL
          AND demo_party IS NOT NULL
        GROUP BY county_name, demo_party
        ORDER BY county_name, voter_count DESC
        """
        
        try:
            df = pd.read_sql_query(query, self.pg_conn)
            logger.info(f"Retrieved county summary data for {len(df)} county-party combinations")
            return df
        except Exception as e:
            logger.error(f"Error retrieving county summary: {e}")
            return pd.DataFrame()
    
    def create_voter_map(self, voter_data: pd.DataFrame, output_file: str = 'voter_map.html'):
        """Create interactive map showing individual voter locations by party."""
        if voter_data.empty:
            logger.warning("No voter data available for mapping")
            return
        
        center_lat = voter_data['latitude'].mean()
        center_lng = voter_data['longitude'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        party_colors = {
            'REPUBLICAN': 'red',
            'DEMOCRAT': 'blue',
            'UNAFFILIATED': 'gray',
            'GREEN': 'green',
            'LIBERTARIAN': 'purple'
        }
        
        for _, voter in voter_data.iterrows():
            party = voter.get('demo_party', 'UNKNOWN')
            color = party_colors.get(party, 'black')
            
            popup_text = f"""
            <b>{voter.get('name_first', '')} {voter.get('name_last', '')}</b><br>
            Party: {party}<br>
            Address: {voter.get('addr_residential_line1', '')}<br>
            City: {voter.get('addr_residential_city', '')}<br>
            County: {voter.get('county_name', '')}<br>
            Accuracy: {voter.get('geocoding_accuracy', '')}
            """
            
            folium.CircleMarker(
                location=[voter['latitude'], voter['longitude']],
                radius=3,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6
            ).add_to(m)
        
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Party Affiliation</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Republican</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Democrat</p>
        <p><i class="fa fa-circle" style="color:gray"></i> Unaffiliated</p>
        <p><i class="fa fa-circle" style="color:green"></i> Green</p>
        <p><i class="fa fa-circle" style="color:purple"></i> Libertarian</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        m.save(output_file)
        logger.info(f"✅ Voter map saved to {output_file}")
    
    def create_county_summary(self, county_data: pd.DataFrame, output_file: str = 'county_summary.html'):
        """Create county-level political distribution charts."""
        if county_data.empty:
            logger.warning("No county data available for summary")
            return
        
        county_totals = county_data.groupby('county_name')['voter_count'].sum().reset_index()
        county_totals = county_totals.sort_values('voter_count', ascending=False)
        
        party_pivot = county_data.pivot(index='county_name', columns='demo_party', values='voter_count').fillna(0)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Voter Count by County', 'Party Distribution by County'),
            specs=[[{"type": "bar"}], [{"type": "bar"}]]
        )
        
        fig.add_trace(
            go.Bar(
                x=county_totals['county_name'],
                y=county_totals['voter_count'],
                name='Total Voters',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        party_colors = {
            'REPUBLICAN': 'red',
            'DEMOCRAT': 'blue',
            'UNAFFILIATED': 'gray',
            'GREEN': 'green',
            'LIBERTARIAN': 'purple'
        }
        
        for party in party_pivot.columns:
            if party in party_colors:
                fig.add_trace(
                    go.Bar(
                        x=party_pivot.index,
                        y=party_pivot[party],
                        name=party,
                        marker_color=party_colors[party]
                    ),
                    row=2, col=1
                )
        
        fig.update_layout(
            height=800,
            title_text="New Jersey Voter Analysis by County",
            showlegend=True
        )
        
        fig.update_xaxes(title_text="County", row=1, col=1)
        fig.update_xaxes(title_text="County", row=2, col=1)
        fig.update_yaxes(title_text="Voter Count", row=1, col=1)
        fig.update_yaxes(title_text="Voter Count", row=2, col=1)
        
        fig.write_html(output_file)
        logger.info(f"✅ County summary saved to {output_file}")
    
    def generate_all_visualizations(self):
        """Generate all visualization files."""
        logger.info("🎨 Starting visualization generation...")
        
        if not self.connect_postgres():
            logger.error("Failed to connect to PostgreSQL")
            return False
        
        try:
            voter_data = self.get_voter_data(limit=5000)
            if not voter_data.empty:
                self.create_voter_map(voter_data)
            else:
                logger.warning("⚠️ No geocoded voter data found for mapping")
            
            county_data = self.get_county_summary()
            if not county_data.empty:
                self.create_county_summary(county_data)
            else:
                logger.warning("⚠️ No county data found for summary")
            
            street_data = self.get_street_data()
            if not street_data.empty:
                logger.info(f"📊 Found {len(street_data)} streets with party data")
            else:
                logger.warning("⚠️ No street-level data found")
            
            logger.info("🎉 Visualization generation complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating visualizations: {e}")
            return False
        finally:
            if self.pg_conn:
                self.pg_conn.close()

def main():
    """Main visualization execution."""
    logger.info("🗺️ PostgreSQL Mapping Visualizations")
    logger.info("=" * 50)
    
    pg_config = {
        'pg_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'pg_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'pg_database': os.getenv('POSTGRES_DATABASE', 'voter_data'),
        'pg_user': os.getenv('POSTGRES_USER', 'postgres'),
        'pg_password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    visualizer = PostgresMappingVisualizations(**pg_config)
    
    success = visualizer.generate_all_visualizations()
    
    if success:
        logger.info("✅ All visualizations generated successfully!")
        logger.info("📁 Output files:")
        logger.info("   - voter_map.html (Interactive voter location map)")
        logger.info("   - county_summary.html (County-level political charts)")
    else:
        logger.error("❌ Visualization generation failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
