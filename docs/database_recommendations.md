# Database Recommendations for NJ Voter Data with Geolocation

## Current Data Profile
- **Records**: 622,304 voters
- **Size**: 290MB CSV (will grow with geolocation data)
- **Fields**: 80 columns including addresses, demographics, voting history
- **Goal**: Street-level political mapping and visualization

## Recommended Database Solutions

### 1. PostgreSQL + PostGIS (Recommended)

**Why PostgreSQL + PostGIS:**
- Industry standard for geospatial data
- Excellent performance for spatial queries
- Rich ecosystem of mapping tools
- Cost-effective (open source)
- Handles complex spatial operations

**Setup:**
```sql
-- Enable PostGIS extension
CREATE EXTENSION postgis;

-- Create voter table with spatial column
CREATE TABLE voters (
    id VARCHAR PRIMARY KEY,
    name_first VARCHAR,
    name_last VARCHAR,
    demo_age INTEGER,
    demo_party VARCHAR,
    demo_gender VARCHAR,
    addr_residential_line1 VARCHAR,
    addr_residential_city VARCHAR,
    county_name VARCHAR,
    zip_code INTEGER,
    -- Spatial columns
    geom GEOMETRY(POINT, 4326),  -- Lat/Long coordinates
    geom_address GEOMETRY(POINT, 4326),  -- Geocoded address
    -- Voting history columns...
);

-- Spatial index for fast queries
CREATE INDEX idx_voters_geom ON voters USING GIST (geom);
```

**Advantages:**
- ✅ Excellent spatial query performance
- ✅ Works with QGIS, Leaflet, Mapbox
- ✅ Can run on GCP Cloud SQL
- ✅ Rich spatial functions (distance, clustering, etc.)
- ✅ JSON support for flexible schema

**Use Cases:**
```sql
-- Find all Republicans within 500m of a point
SELECT * FROM voters 
WHERE demo_party = 'REPUBLICAN' 
AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-74.123, 40.456), 4326), 500);

-- Cluster voters by party within census blocks
SELECT demo_party, COUNT(*), ST_ClusterKMeans(geom, 10) OVER() as cluster
FROM voters GROUP BY demo_party, cluster;
```

### 2. Google BigQuery with Geography Functions

**Why BigQuery:**
- Already in GCP ecosystem
- Handles large datasets efficiently
- Built-in geography functions
- Integrates with Google Maps APIs
- Serverless scaling

**Setup:**
```sql
CREATE TABLE `proj-roth.voter_data.voters` (
    id STRING,
    demo_party STRING,
    demo_age INT64,
    address STRING,
    -- Geography column
    location GEOGRAPHY,
    -- Other columns...
);

-- Spatial queries
SELECT demo_party, COUNT(*) as count
FROM `proj-roth.voter_data.voters`
WHERE ST_DWithin(location, ST_GeogPoint(-74.123, 40.456), 1000)
GROUP BY demo_party;
```

**Advantages:**
- ✅ Serverless and scalable
- ✅ Already in your GCP project
- ✅ Integrates with Data Studio for visualization
- ✅ No infrastructure management

**Disadvantages:**
- ❌ More expensive for frequent queries
- ❌ Less flexible than PostGIS

### 3. MongoDB with Geospatial Indexes

**Why MongoDB:**
- Flexible document structure
- Good geospatial support
- Easy to add new fields
- Works well with Node.js/Python

**Setup:**
```javascript
// Create geospatial index
db.voters.createIndex({ "location": "2dsphere" });

// Query example
db.voters.find({
    "demo_party": "REPUBLICAN",
    "location": {
        $near: {
            $geometry: { type: "Point", coordinates: [-74.123, 40.456] },
            $maxDistance: 1000
        }
    }
});
```

## Geolocation Enhancement Strategy

### 1. Address Geocoding
```python
# Using Google Maps Geocoding API
import googlemaps

def geocode_addresses(df):
    gmaps = googlemaps.Client(key='YOUR_API_KEY')
    
    for idx, row in df.iterrows():
        address = f"{row['addr_residential_line1']}, {row['addr_residential_city']}, NJ {row['zip_code']}"
        result = gmaps.geocode(address)
        
        if result:
            lat = result[0]['geometry']['location']['lat']
            lng = result[0]['geometry']['location']['lng']
            df.at[idx, 'latitude'] = lat
            df.at[idx, 'longitude'] = lng
    
    return df
```

### 2. Census Block Integration
- Add census block FIPS codes
- Demographic overlays
- Voting district boundaries

### 3. Street-Level Aggregation
```sql
-- PostgreSQL example: Party concentration by street
SELECT 
    addr_residential_street_name,
    demo_party,
    COUNT(*) as voter_count,
    ST_Centroid(ST_Collect(geom)) as street_center
FROM voters 
GROUP BY addr_residential_street_name, demo_party
HAVING COUNT(*) > 5;
```

## Visualization Tools

### 1. Leaflet + PostGIS
- Interactive web maps
- Real-time filtering
- Custom markers by party

### 2. QGIS
- Professional GIS analysis
- Heat maps and choropleth maps
- Export to web formats

### 3. Plotly/Folium (Python)
- Programmatic map generation
- Integration with analysis pipeline
- Jupyter notebook compatibility

## Implementation Recommendation

**Phase 1: PostgreSQL + PostGIS Setup**
1. Set up Cloud SQL PostgreSQL instance
2. Enable PostGIS extension
3. Import voter data
4. Geocode addresses using Google Maps API

**Phase 2: Geolocation Enhancement**
1. Batch geocode all addresses
2. Add census block data
3. Create spatial indexes
4. Validate geocoding accuracy

**Phase 3: Mapping Application**
1. Build web interface with Leaflet
2. Create party concentration heat maps
3. Add filtering by demographics
4. Street-level zoom capabilities

## Cost Estimates

**PostgreSQL (Cloud SQL):**
- db-standard-2: ~$100/month
- Storage: ~$10/month
- Geocoding API: ~$500 (one-time for 622K addresses)

**BigQuery:**
- Storage: ~$5/month
- Queries: Variable based on usage
- Geocoding API: ~$500 (one-time)

## Next Steps

1. Choose database platform
2. Set up development environment
3. Create geocoding pipeline
4. Build initial mapping prototype
5. Iterate on visualization features
