import pandas as pd
import numpy as np
import folium
from folium import plugins
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
import json
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class BigQueryVoterMappingVisualizer:
    """Create interactive maps and visualizations for voter data analysis using BigQuery."""
    
    def __init__(self, project_id: str = 'proj-roth', dataset_id: str = 'voter_data'):
        """Initialize the mapping visualizer."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = bigquery.Client(project=project_id)
        
    def get_street_party_data(self, min_voters: int = 5) -> pd.DataFrame:
        """Get street-level party concentration data from BigQuery."""
        query = f"""
        SELECT 
            street_name,
            city,
            county,
            zip_code,
            republican_count,
            democrat_count,
            unaffiliated_count,
            total_voters,
            republican_pct,
            democrat_pct,
            unaffiliated_pct,
            street_center_longitude as longitude,
            street_center_latitude as latitude
        FROM `{self.project_id}.{self.dataset_id}.street_party_summary`
        WHERE total_voters >= {min_voters}
        ORDER BY total_voters DESC
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error querying street party data: {e}")
            return pd.DataFrame()
    
    def get_voter_points(self, sample_size: Optional[int] = None, 
                        party_filter: Optional[str] = None) -> pd.DataFrame:
        """Get individual voter coordinates for point mapping."""
        where_clause = "WHERE latitude IS NOT NULL"
        
        if party_filter:
            where_clause += f" AND demo_party = '{party_filter}'"
        
        limit_clause = ""
        if sample_size:
            limit_clause = f" ORDER BY RAND() LIMIT {sample_size}"
        
        query = f"""
        SELECT 
            id,
            demo_party,
            demo_age,
            demo_gender,
            addr_residential_city,
            county_name,
            latitude,
            longitude
        FROM `{self.project_id}.{self.dataset_id}.voters`
        {where_clause}
        {limit_clause}
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error querying voter points: {e}")
            return pd.DataFrame()
    
    def get_geographic_analysis(self) -> pd.DataFrame:
        """Get geographic analysis data for party concentrations by area."""
        query = f"""
        SELECT 
            county_name,
            demo_party,
            COUNT(*) as voter_count,
            ST_X(ST_CENTROID(ST_UNION_AGG(location))) as center_longitude,
            ST_Y(ST_CENTROID(ST_UNION_AGG(location))) as center_latitude
        FROM `{self.project_id}.{self.dataset_id}.voters`
        WHERE location IS NOT NULL
        GROUP BY county_name, demo_party
        ORDER BY county_name, voter_count DESC
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error querying geographic analysis: {e}")
            return pd.DataFrame()
    
    def create_street_concentration_map(self, output_path: str = "bigquery_street_party_map.html"):
        """Create interactive map showing Republican vs Democrat street concentrations."""
        street_data = self.get_street_party_data(min_voters=5)
        
        if street_data.empty:
            logger.warning("No street data available for mapping")
            return None
        
        center_lat = street_data['latitude'].mean()
        center_lon = street_data['longitude'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        folium.TileLayer('CartoDB positron').add_to(m)
        folium.TileLayer('CartoDB dark_matter').add_to(m)
        
        def get_party_color(row):
            """Determine color based on party dominance."""
            if row['republican_pct'] > row['democrat_pct'] + 10:
                return 'red'  # Strong Republican
            elif row['democrat_pct'] > row['republican_pct'] + 10:
                return 'blue'  # Strong Democrat
            elif row['republican_pct'] > row['democrat_pct']:
                return 'pink'  # Lean Republican
            elif row['democrat_pct'] > row['republican_pct']:
                return 'lightblue'  # Lean Democrat
            else:
                return 'purple'  # Competitive
        
        def get_marker_size(total_voters):
            """Scale marker size based on total voters."""
            return max(5, min(20, total_voters / 2))
        
        for _, row in street_data.iterrows():
            color = get_party_color(row)
            size = get_marker_size(row['total_voters'])
            
            popup_content = f"""
            <b>{row['street_name']}</b><br>
            {row['city']}, {row['county']} County<br>
            <hr>
            <b>Total Voters:</b> {row['total_voters']}<br>
            <b>Republican:</b> {row['republican_count']} ({row['republican_pct']:.1f}%)<br>
            <b>Democrat:</b> {row['democrat_count']} ({row['democrat_pct']:.1f}%)<br>
            <b>Unaffiliated:</b> {row['unaffiliated_count']} ({row['unaffiliated_pct']:.1f}%)<br>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=size,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{row['street_name']} - {row['city']}"
            ).add_to(m)
        
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 140px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Party Concentration</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Strong Republican (>10% lead)</p>
        <p><i class="fa fa-circle" style="color:pink"></i> Lean Republican</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Strong Democrat (>10% lead)</p>
        <p><i class="fa fa-circle" style="color:lightblue"></i> Lean Democrat</p>
        <p><i class="fa fa-circle" style="color:purple"></i> Competitive</p>
        <p><small>Data from BigQuery</small></p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        folium.LayerControl().add_to(m)
        
        m.save(output_path)
        logger.info(f"Street concentration map saved to {output_path}")
        
        return m
    
    def create_party_heatmap(self, party: str = 'REPUBLICAN', output_path: str = "bigquery_party_heatmap.html"):
        """Create density heatmap for specific party."""
        voter_data = self.get_voter_points(sample_size=10000, party_filter=party)
        
        if voter_data.empty:
            logger.warning(f"No voter data available for party: {party}")
            return None
        
        center_lat = voter_data['latitude'].mean()
        center_lon = voter_data['longitude'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        heat_data = [[row['latitude'], row['longitude']] for _, row in voter_data.iterrows()]
        
        plugins.HeatMap(
            heat_data,
            radius=15,
            blur=10,
            max_zoom=1,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}
        ).add_to(m)
        
        title_html = f'''
        <h3 align="center" style="font-size:20px"><b>{party} Voter Density Heatmap</b></h3>
        <p align="center" style="font-size:14px">Data from BigQuery - NJ Congressional District 07</p>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        m.save(output_path)
        logger.info(f"{party} heatmap saved to {output_path}")
        
        return m
    
    def create_comparative_analysis_dashboard(self, output_path: str = "bigquery_party_analysis_dashboard.html"):
        """Create comprehensive dashboard comparing party distributions."""
        street_data = self.get_street_party_data(min_voters=3)
        geo_data = self.get_geographic_analysis()
        
        if street_data.empty:
            logger.warning("No data available for dashboard")
            return None
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Party Dominance by Street Count',
                'Voter Distribution by County & Party',
                'Republican vs Democrat Street Percentages',
                'Street-Level Competitiveness Distribution',
                'Geographic Party Centers by County',
                'Top Republican vs Democrat Streets'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        party_dominance = []
        for _, row in street_data.iterrows():
            if row['republican_pct'] > row['democrat_pct'] + 5:
                party_dominance.append('Republican')
            elif row['democrat_pct'] > row['republican_pct'] + 5:
                party_dominance.append('Democrat')
            else:
                party_dominance.append('Competitive')
        
        dominance_counts = pd.Series(party_dominance).value_counts()
        
        fig.add_trace(
            go.Bar(x=dominance_counts.index, y=dominance_counts.values,
                   marker_color=['red', 'blue', 'purple']),
            row=1, col=1
        )
        
        if not geo_data.empty:
            county_party_pivot = geo_data.pivot(index='county_name', columns='demo_party', values='voter_count').fillna(0)
            
            for party in ['REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED']:
                if party in county_party_pivot.columns:
                    fig.add_trace(
                        go.Bar(x=county_party_pivot.index, y=county_party_pivot[party],
                               name=party, showlegend=False),
                        row=1, col=2
                    )
        
        fig.add_trace(
            go.Scatter(
                x=street_data['republican_pct'],
                y=street_data['democrat_pct'],
                mode='markers',
                marker=dict(
                    size=street_data['total_voters']/2,
                    color=street_data['total_voters'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Total Voters")
                ),
                text=street_data['street_name'] + ', ' + street_data['city'],
                hovertemplate='<b>%{text}</b><br>Republican: %{x:.1f}%<br>Democrat: %{y:.1f}%<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=[0, 100], y=[0, 100], mode='lines', 
                      line=dict(dash='dash', color='gray'),
                      showlegend=False),
            row=2, col=1
        )
        
        competitiveness = abs(street_data['republican_pct'] - street_data['democrat_pct'])
        
        fig.add_trace(
            go.Histogram(x=competitiveness, nbinsx=20, marker_color='orange', showlegend=False),
            row=2, col=2
        )
        
        if not geo_data.empty:
            for party in ['REPUBLICAN', 'DEMOCRAT']:
                party_data = geo_data[geo_data['demo_party'] == party]
                if not party_data.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=party_data['center_longitude'],
                            y=party_data['center_latitude'],
                            mode='markers+text',
                            marker=dict(
                                size=party_data['voter_count']/1000,
                                color='red' if party == 'REPUBLICAN' else 'blue'
                            ),
                            text=party_data['county_name'],
                            textposition="top center",
                            name=party,
                            showlegend=False
                        ),
                        row=3, col=1
                    )
        
        top_republican = street_data.nlargest(10, 'republican_pct')
        top_democrat = street_data.nlargest(10, 'democrat_pct')
        
        fig.add_trace(
            go.Bar(
                y=top_republican['street_name'] + ', ' + top_republican['city'],
                x=top_republican['republican_pct'],
                orientation='h',
                marker_color='red',
                name='Republican',
                showlegend=False
            ),
            row=3, col=2
        )
        
        fig.update_layout(
            title_text="NJ Congressional District 07 - BigQuery Street-Level Political Analysis",
            title_x=0.5,
            height=1200,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Party Dominance", row=1, col=1)
        fig.update_yaxes(title_text="Number of Streets", row=1, col=1)
        
        fig.update_xaxes(title_text="County", row=1, col=2)
        fig.update_yaxes(title_text="Voter Count", row=1, col=2)
        
        fig.update_xaxes(title_text="Republican %", row=2, col=1)
        fig.update_yaxes(title_text="Democrat %", row=2, col=1)
        
        fig.update_xaxes(title_text="Percentage Point Difference", row=2, col=2)
        fig.update_yaxes(title_text="Number of Streets", row=2, col=2)
        
        fig.update_xaxes(title_text="Longitude", row=3, col=1)
        fig.update_yaxes(title_text="Latitude", row=3, col=1)
        
        fig.update_xaxes(title_text="Republican %", row=3, col=2)
        fig.update_yaxes(title_text="Street", row=3, col=2)
        
        fig.write_html(output_path)
        logger.info(f"Analysis dashboard saved to {output_path}")
        
        return fig
    
    def generate_summary_report(self) -> Dict:
        """Generate summary statistics for mapping analysis."""
        query = f"""
        SELECT 
            COUNT(*) as total_streets,
            SUM(total_voters) as total_mapped_voters,
            AVG(republican_pct) as avg_republican_pct,
            AVG(democrat_pct) as avg_democrat_pct,
            COUNTIF(republican_pct > democrat_pct + 10) as strong_republican_streets,
            COUNTIF(democrat_pct > republican_pct + 10) as strong_democrat_streets,
            COUNTIF(ABS(republican_pct - democrat_pct) <= 10) as competitive_streets
        FROM `{self.project_id}.{self.dataset_id}.street_party_summary`
        WHERE total_voters >= 5
        """
        
        try:
            result = self.bq_client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                return {
                    'total_streets': int(row['total_streets']),
                    'total_mapped_voters': int(row['total_mapped_voters']),
                    'average_republican_percentage': round(row['avg_republican_pct'], 2),
                    'average_democrat_percentage': round(row['avg_democrat_pct'], 2),
                    'strong_republican_streets': int(row['strong_republican_streets']),
                    'strong_democrat_streets': int(row['strong_democrat_streets']),
                    'competitive_streets': int(row['competitive_streets'])
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return {}

def main():
    """Example usage of the BigQuery mapping visualizer."""
    visualizer = BigQueryVoterMappingVisualizer(
        project_id='proj-roth',
        dataset_id='voter_data'
    )
    
    visualizer.create_street_concentration_map("nj07_bigquery_street_party_map.html")
    visualizer.create_party_heatmap("REPUBLICAN", "republican_bigquery_heatmap.html")
    visualizer.create_party_heatmap("DEMOCRAT", "democrat_bigquery_heatmap.html")
    visualizer.create_comparative_analysis_dashboard("bigquery_party_analysis_dashboard.html")
    
    summary = visualizer.generate_summary_report()
    print("BigQuery Mapping Analysis Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
