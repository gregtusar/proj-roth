# BigQuery Implementation for NJ Voter Data Analysis

This document describes the BigQuery implementation for storing and analyzing New Jersey voter data with geolocation capabilities for street-level political mapping.

## Overview

The BigQuery solution provides:
- **Scalable Data Storage**: Handle 622K+ voter records with room for growth
- **Spatial Analysis**: Built-in geography functions for location-based queries
- **Cost-Effective**: Serverless architecture with pay-per-query pricing
- **GCP Integration**: Seamless integration with existing GCP infrastructure
- **Real-time Analytics**: Fast queries for interactive mapping applications

## Architecture

```
GCP Bucket (nj7voterfile) 
    ↓
BigQuery Dataset (voter_data)
    ├── voters (main table with geolocation)
    └── street_party_summary (aggregated street-level data)
    ↓
Mapping Applications (Folium, Plotly, Leaflet)
```

## Files Structure

### Core Implementation
- **`bigquery_schema.sql`** - Database schema with spatial columns
- **`bigquery_geocoding_pipeline.py`** - Data import and geocoding pipeline
- **`bigquery_mapping_visualization.py`** - Interactive mapping and visualization
- **`setup_bigquery_environment.py`** - One-click environment setup

### Configuration
- **`database_recommendations.md`** - Comparison of database options
- **`README_bigquery.md`** - This implementation guide

## Quick Start

### 1. Environment Setup

```bash
# Install required packages
pip install google-cloud-bigquery googlemaps folium plotly pandas

# Set up BigQuery environment
python setup_bigquery_environment.py
```

### 2. Import Voter Data

```python
from bigquery_geocoding_pipeline import BigQueryVoterGeocodingPipeline

# Initialize pipeline
pipeline = BigQueryVoterGeocodingPipeline(
    project_id='proj-roth',
    dataset_id='voter_data',
    google_api_key='YOUR_GOOGLE_MAPS_API_KEY'
)

# Import data from CSV
pipeline.import_voters_to_bigquery(df)
```

### 3. Geocode Addresses

```python
# Geocode voter addresses in batches
while True:
    stats = pipeline.get_geocoding_stats()
    if stats['remaining_voters'] == 0:
        break
    
    pipeline.geocode_voters_batch(batch_size=100)
    time.sleep(1)  # Rate limiting

# Generate street-level summary
pipeline.refresh_street_summary()
```

### 4. Create Visualizations

```python
from bigquery_mapping_visualization import BigQueryVoterMappingVisualizer

visualizer = BigQueryVoterMappingVisualizer()

# Create interactive maps
visualizer.create_street_concentration_map("street_map.html")
visualizer.create_party_heatmap("REPUBLICAN", "republican_heatmap.html")
visualizer.create_comparative_analysis_dashboard("dashboard.html")
```

## Database Schema

### Main Tables

#### `voters` Table
- **Primary Data**: All 80 original voter file columns
- **Geolocation**: `latitude`, `longitude`, `location` (GEOGRAPHY)
- **Geocoding Metadata**: accuracy, source, confidence, date
- **Indexes**: Clustered by `demo_party` and `county_name`

#### `street_party_summary` Table
- **Aggregated Data**: Party counts and percentages by street
- **Geographic Center**: Street-level centroid coordinates
- **Performance**: Pre-calculated for fast mapping queries

### Key Spatial Columns

```sql
-- Geographic point for spatial queries
location GEOGRAPHY,

-- Separate coordinates for easy access
latitude FLOAT64,
longitude FLOAT64,

-- Geocoding quality metrics
geocoding_accuracy STRING,  -- ROOFTOP, RANGE_INTERPOLATED, etc.
geocoding_confidence FLOAT64  -- 0.0 to 1.0
```

## Spatial Queries

### Find Nearby Voters
```sql
SELECT demo_party, COUNT(*) as count
FROM `proj-roth.voter_data.voters`
WHERE ST_DWITHIN(
  location, 
  ST_GEOGPOINT(-74.123, 40.456), 
  500  -- 500 meters
)
GROUP BY demo_party;
```

### Street-Level Analysis
```sql
SELECT 
  street_name,
  republican_pct,
  democrat_pct,
  total_voters
FROM `proj-roth.voter_data.street_party_summary`
WHERE total_voters >= 10
ORDER BY republican_pct DESC;
```

### Geographic Clustering
```sql
SELECT 
  county_name,
  demo_party,
  ST_CENTROID(ST_UNION_AGG(location)) as party_center
FROM `proj-roth.voter_data.voters`
WHERE location IS NOT NULL
GROUP BY county_name, demo_party;
```

## Geocoding Strategy

### Primary: Google Maps API
- **Accuracy**: Highest quality geocoding
- **Rate Limit**: 10 requests/second (configurable)
- **Cost**: ~$500 for 622K addresses (one-time)
- **Confidence Scoring**: ROOFTOP (1.0) to APPROXIMATE (0.4)

### Fallback: US Census API
- **Cost**: Free
- **Accuracy**: Good for most addresses
- **Rate Limit**: Generous for batch processing
- **Confidence**: Fixed at 0.7

### Batch Processing
- **Parallel Processing**: 5 concurrent workers
- **Error Handling**: Retry failed geocoding attempts
- **Progress Tracking**: Real-time statistics and logging

## Visualization Capabilities

### Interactive Maps (Folium)
- **Street Concentration**: Color-coded by party dominance
- **Density Heatmaps**: Voter distribution by party
- **Popup Details**: Street-level statistics
- **Multiple Layers**: Different base maps and overlays

### Analytics Dashboard (Plotly)
- **Party Distribution**: Bar charts and pie charts
- **Geographic Analysis**: Scatter plots with coordinates
- **Competitiveness**: Histogram of party margins
- **County Comparison**: Multi-panel analysis

### Export Formats
- **HTML**: Interactive web maps
- **PNG/PDF**: Static images for reports
- **JSON**: Data export for external tools

## Performance Optimization

### BigQuery Optimizations
- **Clustering**: Tables clustered by frequently queried columns
- **Partitioning**: Consider date partitioning for time-series analysis
- **Materialized Views**: Pre-computed aggregations for common queries

### Query Best Practices
- **Spatial Indexes**: Automatic optimization for geography columns
- **Projection**: Select only needed columns
- **Filtering**: Use WHERE clauses to limit data scanned

### Cost Management
- **Query Optimization**: Monitor and optimize expensive queries
- **Data Lifecycle**: Archive old data if needed
- **Slot Reservations**: Consider for predictable workloads

## Security and Access Control

### IAM Roles
- **BigQuery Data Editor**: For data import and updates
- **BigQuery User**: For running queries and analysis
- **Storage Object Viewer**: For accessing source data

### Data Privacy
- **Address Aggregation**: Street-level summaries (min 3 voters)
- **Geocoding Accuracy**: Balance precision with privacy
- **Access Logging**: Monitor data access patterns

## Monitoring and Maintenance

### Data Quality Checks
- **Geocoding Success Rate**: Monitor completion percentage
- **Accuracy Distribution**: Track geocoding confidence scores
- **Data Freshness**: Update timestamps and data lineage

### Regular Tasks
- **Street Summary Refresh**: Update aggregated tables
- **Geocoding Retries**: Process failed addresses
- **Performance Monitoring**: Query performance and costs

## Integration with Existing Workflow

### GCP Data Pipeline
1. **Source**: Voter data in GCS bucket (`nj7voterfile`)
2. **Processing**: BigQuery for storage and analysis
3. **Visualization**: Web applications and dashboards
4. **Export**: Results back to GCS or external systems

### Development Workflow
1. **Local Development**: Test with sample data
2. **Staging**: Validate with full dataset
3. **Production**: Deploy to production BigQuery
4. **Monitoring**: Track performance and usage

## Cost Estimation

### Storage Costs
- **Voter Data**: ~$5/month for 622K records
- **Growth**: Scales linearly with data volume

### Query Costs
- **Analysis Queries**: ~$0.01-0.10 per query
- **Geocoding Updates**: One-time cost for batch processing
- **Interactive Dashboards**: Variable based on usage

### API Costs
- **Google Maps Geocoding**: ~$500 one-time for full dataset
- **Ongoing Updates**: Minimal for new registrations

## Next Steps

1. **Complete Setup**: Run `setup_bigquery_environment.py`
2. **Import Data**: Load voter data from CSV
3. **Geocode Addresses**: Process all voter addresses
4. **Create Visualizations**: Generate interactive maps
5. **Deploy Applications**: Host mapping applications
6. **Monitor Performance**: Track usage and optimize

## Support and Troubleshooting

### Common Issues
- **Authentication**: Ensure service account has proper permissions
- **Rate Limits**: Adjust geocoding batch sizes if needed
- **Memory**: Use chunked processing for large datasets

### Debugging
- **Logging**: Comprehensive logging throughout pipeline
- **Error Handling**: Graceful failure recovery
- **Monitoring**: BigQuery job monitoring and alerting

---

*BigQuery implementation for NJ Congressional District 07 voter analysis*
