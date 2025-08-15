

CREATE OR REPLACE TABLE `proj-roth.voter_data.voters` (
  id STRING NOT NULL,
  
  name_first STRING,
  name_middle STRING,
  name_last STRING,
  
  demo_age INT64,
  demo_race STRING,
  demo_race_confidence STRING,
  demo_gender STRING,
  demo_party STRING,
  
  addr_residential_street_name STRING,
  addr_residential_street_number STRING,
  addr_residential_line1 STRING,
  addr_residential_line2 STRING,
  addr_residential_line3 STRING,
  addr_residential_city STRING,
  addr_residential_state STRING,
  addr_residential_zip_code INT64,
  
  county_name STRING,
  congressional_name STRING,
  state_house_name STRING,
  state_senate_name STRING,
  precinct_name STRING,
  municipal_name STRING,
  place_name STRING,
  city_council_name STRING,
  
  email STRING,
  phone_1 INT64,
  phone_2 INT64,
  
  registration_status_civitech STRING,
  voter_type STRING,
  
  current_voter_registration_intent FLOAT64,
  current_support_score FLOAT64,
  current_tags STRING,
  score_support_generic_dem FLOAT64,
  
  participation_primary_2016 BOOL,
  participation_primary_2017 BOOL,
  participation_primary_2018 BOOL,
  participation_primary_2019 BOOL,
  participation_primary_2020 BOOL,
  participation_primary_2021 BOOL,
  participation_primary_2022 BOOL,
  participation_primary_2023 BOOL,
  participation_primary_2024 BOOL,
  
  participation_general_2016 BOOL,
  participation_general_2017 BOOL,
  participation_general_2018 BOOL,
  participation_general_2019 BOOL,
  participation_general_2020 BOOL,
  participation_general_2021 BOOL,
  participation_general_2022 BOOL,
  participation_general_2023 BOOL,
  participation_general_2024 BOOL,
  
  vote_primary_dem_2016 BOOL,
  vote_primary_rep_2016 BOOL,
  vote_primary_dem_2017 BOOL,
  vote_primary_rep_2017 BOOL,
  vote_primary_dem_2018 BOOL,
  vote_primary_rep_2018 BOOL,
  vote_primary_dem_2019 BOOL,
  vote_primary_rep_2019 BOOL,
  vote_primary_dem_2020 BOOL,
  vote_primary_rep_2020 BOOL,
  vote_primary_dem_2021 BOOL,
  vote_primary_rep_2021 BOOL,
  vote_primary_dem_2022 BOOL,
  vote_primary_rep_2022 BOOL,
  vote_primary_dem_2023 BOOL,
  vote_primary_rep_2023 BOOL,
  vote_primary_dem_2024 BOOL,
  vote_primary_rep_2024 BOOL,
  
  vote_other_2016 STRING,
  vote_other_2017 STRING,
  vote_other_2018 STRING,
  vote_other_2019 STRING,
  vote_other_2020 STRING,
  vote_other_2021 STRING,
  vote_other_2022 STRING,
  vote_other_2023 STRING,
  vote_other_2024 STRING,
  
  notes STRING,
  
  location GEOGRAPHY,
  
  latitude FLOAT64,
  longitude FLOAT64,
  
  geocoding_accuracy STRING, -- ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
  geocoding_source STRING,   -- GOOGLE_MAPS, CENSUS, etc.
  geocoding_date TIMESTAMP,
  geocoding_confidence FLOAT64, -- 0.0 to 1.0
  
  standardized_address STRING,
  
  census_block_fips STRING,
  census_tract_fips STRING,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY demo_party, county_name;

CREATE OR REPLACE TABLE `proj-roth.voter_data.street_party_summary` (
  street_name STRING,
  city STRING,
  county STRING,
  zip_code INT64,
  
  republican_count INT64,
  democrat_count INT64,
  unaffiliated_count INT64,
  other_party_count INT64,
  total_voters INT64,
  
  republican_pct FLOAT64,
  democrat_pct FLOAT64,
  unaffiliated_pct FLOAT64,
  
  street_center_location GEOGRAPHY,
  street_center_latitude FLOAT64,
  street_center_longitude FLOAT64,
  
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY county, republican_pct DESC;


/*
SELECT 
  demo_party,
  COUNT(*) as voter_count,
  ST_X(ST_CENTROID(ST_UNION_AGG(location))) as center_lng,
  ST_Y(ST_CENTROID(ST_UNION_AGG(location))) as center_lat
FROM `proj-roth.voter_data.voters`
WHERE ST_DWITHIN(
  location, 
  ST_GEOGPOINT(-74.123, 40.456), 
  500  -- 500 meters
)
GROUP BY demo_party;
*/

/*
SELECT 
  street_name,
  city,
  republican_count,
  democrat_count,
  republican_pct,
  street_center_longitude as lng,
  street_center_latitude as lat
FROM `proj-roth.voter_data.street_party_summary`
WHERE total_voters >= 10
ORDER BY republican_pct DESC 
LIMIT 20;
*/

/*
SELECT 
  v1.id,
  v1.name_first,
  v1.name_last,
  v1.addr_residential_line1,
  v1.demo_party,
  ST_DISTANCE(v1.location, v2.location) as distance_meters
FROM `proj-roth.voter_data.voters` v1
CROSS JOIN `proj-roth.voter_data.voters` v2
WHERE v1.demo_party = 'REPUBLICAN' 
  AND v2.demo_party = 'DEMOCRAT'
  AND ST_DWITHIN(v1.location, v2.location, 100)  -- Within 100m
  AND v1.id != v2.id
ORDER BY distance_meters
LIMIT 100;
*/

/*
CREATE OR REPLACE TABLE `proj-roth.voter_data.street_party_summary` AS
SELECT 
  addr_residential_street_name as street_name,
  addr_residential_city as city,
  county_name as county,
  addr_residential_zip_code as zip_code,
  
  COUNTIF(demo_party = 'REPUBLICAN') as republican_count,
  COUNTIF(demo_party = 'DEMOCRAT') as democrat_count,
  COUNTIF(demo_party = 'UNAFFILIATED') as unaffiliated_count,
  COUNTIF(demo_party NOT IN ('REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED')) as other_party_count,
  COUNT(*) as total_voters,
  
  ROUND(COUNTIF(demo_party = 'REPUBLICAN') * 100.0 / COUNT(*), 2) as republican_pct,
  ROUND(COUNTIF(demo_party = 'DEMOCRAT') * 100.0 / COUNT(*), 2) as democrat_pct,
  ROUND(COUNTIF(demo_party = 'UNAFFILIATED') * 100.0 / COUNT(*), 2) as unaffiliated_pct,
  
  ST_CENTROID(ST_UNION_AGG(location)) as street_center_location,
  ST_X(ST_CENTROID(ST_UNION_AGG(location))) as street_center_longitude,
  ST_Y(ST_CENTROID(ST_UNION_AGG(location))) as street_center_latitude,
  
  CURRENT_TIMESTAMP() as last_updated
  
FROM `proj-roth.voter_data.voters`
WHERE addr_residential_street_name IS NOT NULL 
  AND location IS NOT NULL
GROUP BY addr_residential_street_name, addr_residential_city, county_name, addr_residential_zip_code
HAVING COUNT(*) >= 3; -- Only include streets with 3+ voters for privacy
*/

/*
SELECT 
  demo_party,
  county_name,
  COUNT(*) as voter_count,
  ST_CENTROID(ST_UNION_AGG(location)) as party_center,
  ST_X(ST_CENTROID(ST_UNION_AGG(location))) as center_lng,
  ST_Y(ST_CENTROID(ST_UNION_AGG(location))) as center_lat
FROM `proj-roth.voter_data.voters`
WHERE location IS NOT NULL
GROUP BY demo_party, county_name
ORDER BY county_name, voter_count DESC;
*/
