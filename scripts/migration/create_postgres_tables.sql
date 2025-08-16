
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS voters (
    id VARCHAR NOT NULL PRIMARY KEY,
    
    name_first VARCHAR,
    name_middle VARCHAR,
    name_last VARCHAR,
    
    demo_age INTEGER,
    demo_race VARCHAR,
    demo_race_confidence VARCHAR,
    demo_gender VARCHAR,
    demo_party VARCHAR,
    
    addr_residential_street_name VARCHAR,
    addr_residential_street_number VARCHAR,
    addr_residential_line1 VARCHAR,
    addr_residential_line2 VARCHAR,
    addr_residential_line3 VARCHAR,
    addr_residential_city VARCHAR,
    addr_residential_state VARCHAR,
    addr_residential_zip_code INTEGER,
    
    county_name VARCHAR,
    congressional_name VARCHAR,
    state_house_name VARCHAR,
    state_senate_name VARCHAR,
    precinct_name VARCHAR,
    municipal_name VARCHAR,
    place_name VARCHAR,
    city_council_name VARCHAR,
    
    email VARCHAR,
    phone_1 BIGINT,
    phone_2 BIGINT,
    
    registration_status_civitech VARCHAR,
    voter_type VARCHAR,
    
    current_voter_registration_intent DOUBLE PRECISION,
    current_support_score DOUBLE PRECISION,
    current_tags VARCHAR,
    score_support_generic_dem DOUBLE PRECISION,
    
    participation_primary_2016 BOOLEAN,
    participation_primary_2017 BOOLEAN,
    participation_primary_2018 BOOLEAN,
    participation_primary_2019 BOOLEAN,
    participation_primary_2020 BOOLEAN,
    participation_primary_2021 BOOLEAN,
    participation_primary_2022 BOOLEAN,
    participation_primary_2023 BOOLEAN,
    participation_primary_2024 BOOLEAN,
    
    participation_general_2016 BOOLEAN,
    participation_general_2017 BOOLEAN,
    participation_general_2018 BOOLEAN,
    participation_general_2019 BOOLEAN,
    participation_general_2020 BOOLEAN,
    participation_general_2021 BOOLEAN,
    participation_general_2022 BOOLEAN,
    participation_general_2023 BOOLEAN,
    participation_general_2024 BOOLEAN,
    
    vote_primary_dem_2016 BOOLEAN,
    vote_primary_dem_2017 BOOLEAN,
    vote_primary_dem_2018 BOOLEAN,
    vote_primary_dem_2019 BOOLEAN,
    vote_primary_dem_2020 BOOLEAN,
    vote_primary_dem_2021 BOOLEAN,
    vote_primary_dem_2022 BOOLEAN,
    vote_primary_dem_2023 BOOLEAN,
    vote_primary_dem_2024 BOOLEAN,
    
    vote_primary_rep_2016 BOOLEAN,
    vote_primary_rep_2017 BOOLEAN,
    vote_primary_rep_2018 BOOLEAN,
    vote_primary_rep_2019 BOOLEAN,
    vote_primary_rep_2020 BOOLEAN,
    vote_primary_rep_2021 BOOLEAN,
    vote_primary_rep_2022 BOOLEAN,
    vote_primary_rep_2023 BOOLEAN,
    vote_primary_rep_2024 BOOLEAN,
    
    vote_other_2016 VARCHAR,
    vote_other_2017 VARCHAR,
    vote_other_2018 VARCHAR,
    vote_other_2019 VARCHAR,
    vote_other_2020 VARCHAR,
    vote_other_2021 VARCHAR,
    vote_other_2022 VARCHAR,
    vote_other_2023 VARCHAR,
    vote_other_2024 VARCHAR,
    
    notes TEXT,
    
    location GEOMETRY(POINT, 4326),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geocoding_accuracy VARCHAR,
    geocoding_source VARCHAR,
    geocoding_date TIMESTAMP,
    geocoding_confidence DOUBLE PRECISION,
    standardized_address TEXT,
    
    census_block_fips VARCHAR,
    census_tract_fips VARCHAR,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voters_party ON voters(demo_party);
CREATE INDEX IF NOT EXISTS idx_voters_county ON voters(county_name);
CREATE INDEX IF NOT EXISTS idx_voters_city ON voters(addr_residential_city);
CREATE INDEX IF NOT EXISTS idx_voters_zip ON voters(addr_residential_zip_code);
CREATE INDEX IF NOT EXISTS idx_voters_geocoded ON voters(latitude, longitude) WHERE latitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_voters_needs_geocoding ON voters(id) WHERE latitude IS NULL;

CREATE INDEX IF NOT EXISTS idx_voters_geom ON voters USING GIST(geom);

CREATE TABLE IF NOT EXISTS street_party_summary (
    id SERIAL PRIMARY KEY,
    street_name VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    county VARCHAR NOT NULL,
    zip_code VARCHAR(10),
    
    republican_count INTEGER DEFAULT 0,
    democrat_count INTEGER DEFAULT 0,
    unaffiliated_count INTEGER DEFAULT 0,
    other_party_count INTEGER DEFAULT 0,
    total_voters INTEGER DEFAULT 0,
    
    republican_pct DECIMAL(5,2) DEFAULT 0,
    democrat_pct DECIMAL(5,2) DEFAULT 0,
    unaffiliated_pct DECIMAL(5,2) DEFAULT 0,
    
    street_center_latitude DOUBLE PRECISION,
    street_center_longitude DOUBLE PRECISION,
    street_center_geom GEOMETRY(POINT, 4326),
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(street_name, city, county, zip_code)
);

CREATE INDEX IF NOT EXISTS idx_street_summary_county ON street_party_summary(county);
CREATE INDEX IF NOT EXISTS idx_street_summary_city ON street_party_summary(city);
CREATE INDEX IF NOT EXISTS idx_street_summary_geom ON street_party_summary USING GIST(street_center_geom);

CREATE OR REPLACE FUNCTION update_voter_geometry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    ELSE
        NEW.geom = NULL;
    END IF;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_voter_geometry
    BEFORE INSERT OR UPDATE ON voters
    FOR EACH ROW
    EXECUTE FUNCTION update_voter_geometry();

CREATE OR REPLACE FUNCTION refresh_street_party_summary()
RETURNS VOID AS $$
BEGIN
    TRUNCATE street_party_summary;
    
    INSERT INTO street_party_summary (
        street_name, city, county, zip_code,
        republican_count, democrat_count, unaffiliated_count, other_party_count, total_voters,
        republican_pct, democrat_pct, unaffiliated_pct,
        street_center_latitude, street_center_longitude, street_center_geom
    )
    SELECT 
        addr_residential_street_name,
        addr_residential_city,
        county_name,
        addr_residential_zip_code,
        
        COUNT(CASE WHEN demo_party = 'REPUBLICAN' THEN 1 END) as republican_count,
        COUNT(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 END) as democrat_count,
        COUNT(CASE WHEN demo_party = 'UNAFFILIATED' THEN 1 END) as unaffiliated_count,
        COUNT(CASE WHEN demo_party NOT IN ('REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED') THEN 1 END) as other_party_count,
        COUNT(*) as total_voters,
        
        ROUND(COUNT(CASE WHEN demo_party = 'REPUBLICAN' THEN 1 END) * 100.0 / COUNT(*), 2) as republican_pct,
        ROUND(COUNT(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 END) * 100.0 / COUNT(*), 2) as democrat_pct,
        ROUND(COUNT(CASE WHEN demo_party = 'UNAFFILIATED' THEN 1 END) * 100.0 / COUNT(*), 2) as unaffiliated_pct,
        
        AVG(latitude) as street_center_latitude,
        AVG(longitude) as street_center_longitude,
        ST_SetSRID(ST_MakePoint(AVG(longitude), AVG(latitude)), 4326) as street_center_geom
        
    FROM voters
    WHERE addr_residential_street_name IS NOT NULL 
      AND latitude IS NOT NULL 
      AND longitude IS NOT NULL
    GROUP BY addr_residential_street_name, addr_residential_city, county_name, addr_residential_zip_code
    HAVING COUNT(*) >= 3;
    
END;
$$ LANGUAGE plpgsql;


COMMENT ON TABLE voters IS 'Main voter registration table migrated from BigQuery';
COMMENT ON TABLE street_party_summary IS 'Street-level party affiliation summary table';
COMMENT ON FUNCTION refresh_street_party_summary() IS 'Rebuilds street party summary from current voter data';
