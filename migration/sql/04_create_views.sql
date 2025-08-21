-- Create views for simplified access and backward compatibility

-- 1. Main voter geospatial view - combines all tables for easy querying
CREATE OR REPLACE VIEW `proj-roth.voter_data.voter_geo_view` AS
SELECT 
  -- Voter info
  v.voter_record_id,
  v.vendor_voter_id,
  v.master_id,
  v.address_id,
  
  -- Individual info
  i.standardized_name,
  i.name_first,
  i.name_middle,
  i.name_last,
  i.name_suffix,
  
  -- Address info
  a.standardized_address,
  a.street_number,
  a.street_name,
  a.city,
  a.state,
  a.zip_code,
  a.county AS address_county,
  a.geo_location,
  a.latitude,
  a.longitude,
  
  -- Voter demographics
  v.demo_party,
  v.demo_age,
  v.demo_race,
  v.demo_gender,
  v.registration_status,
  v.voter_type,
  
  -- Districts
  v.congressional_district,
  v.state_house_district,
  v.state_senate_district,
  v.precinct,
  v.municipal_name,
  v.county_name,
  
  -- Scores
  v.score_support_generic_dem,
  v.current_support_score,
  
  -- Voting history (all participation and vote columns)
  v.participation_primary_2016,
  v.participation_primary_2017,
  v.participation_primary_2018,
  v.participation_primary_2019,
  v.participation_primary_2020,
  v.participation_primary_2021,
  v.participation_primary_2022,
  v.participation_primary_2023,
  v.participation_primary_2024,
  v.participation_general_2016,
  v.participation_general_2017,
  v.participation_general_2018,
  v.participation_general_2019,
  v.participation_general_2020,
  v.participation_general_2021,
  v.participation_general_2022,
  v.participation_general_2023,
  v.participation_general_2024,
  
  -- Metadata
  v.created_at,
  v.updated_at
FROM `proj-roth.voter_data.voters` v
JOIN `proj-roth.voter_data.individuals` i ON v.master_id = i.master_id
JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id;

-- 2. Donor view - combines donation info with individuals
CREATE OR REPLACE VIEW `proj-roth.voter_data.donor_view` AS
SELECT 
  d.donation_record_id,
  d.master_id,
  d.address_id,
  
  -- Individual info (if matched)
  i.standardized_name,
  i.name_first,
  i.name_middle,
  i.name_last,
  
  -- Address info (if matched)
  a.standardized_address,
  a.city,
  a.state,
  a.zip_code,
  a.geo_location,
  
  -- Donation info
  d.committee_name,
  d.contribution_amount,
  d.election_type,
  d.election_year,
  d.employer,
  d.occupation,
  d.donation_date,
  
  -- Original info for unmatched
  d.original_full_name,
  d.original_address,
  d.match_confidence,
  d.match_method,
  
  -- Check if this donor is also a voter
  CASE WHEN v.voter_record_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_registered_voter,
  v.demo_party AS voter_party,
  v.county_name AS voter_county
  
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.addresses` a ON d.address_id = a.address_id
LEFT JOIN `proj-roth.voter_data.voters` v ON d.master_id = v.master_id;

-- 3. Street summary view (recreate existing functionality)
CREATE OR REPLACE VIEW `proj-roth.voter_data.street_party_summary_new` AS
SELECT 
  a.county AS county_name,
  a.city,
  a.street_name,
  COUNT(DISTINCT v.master_id) AS total_voters,
  COUNTIF(v.demo_party = 'DEMOCRAT') AS democrat_count,
  COUNTIF(v.demo_party = 'REPUBLICAN') AS republican_count,
  COUNTIF(v.demo_party = 'UNAFFILIATED') AS unaffiliated_count,
  COUNTIF(v.demo_party NOT IN ('DEMOCRAT', 'REPUBLICAN', 'UNAFFILIATED')) AS other_party_count,
  AVG(v.score_support_generic_dem) AS avg_dem_support_score,
  -- Participation rates
  AVG(CAST(v.participation_general_2020 AS INT64)) AS participation_rate_2020,
  AVG(CAST(v.participation_general_2022 AS INT64)) AS participation_rate_2022,
  AVG(CAST(v.participation_general_2024 AS INT64)) AS participation_rate_2024
FROM `proj-roth.voter_data.voters` v
JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id
GROUP BY county_name, city, street_name;

-- 4. Backward compatibility view (mimics original voters table structure)
CREATE OR REPLACE VIEW `proj-roth.voter_data.voters_compat` AS
SELECT 
  v.vendor_voter_id AS id,
  a.street_name AS addr_residential_street_name,
  a.street_number AS addr_residential_street_number,
  i.name_first,
  i.name_middle,
  i.name_last,
  v.demo_age,
  v.demo_race,
  v.demo_race_confidence,
  v.demo_gender,
  a.state AS addr_residential_state,
  a.city AS addr_residential_city,
  NULL AS current_voter_registration_intent,
  v.current_support_score,
  NULL AS current_tags,
  v.score_support_generic_dem,
  v.demo_party,
  v.registration_status AS registration_status_civitech,
  a.standardized_address AS addr_residential_line1,
  NULL AS addr_residential_line2,
  NULL AS addr_residential_line3,
  a.zip_code AS addr_residential_zip_code,
  v.county_name,
  v.email,
  v.phone_1,
  v.phone_2,
  v.congressional_district AS congressional_name,
  v.state_house_district AS state_house_name,
  v.state_senate_district AS state_senate_name,
  v.precinct AS precinct_name,
  v.municipal_name,
  NULL AS place_name,
  v.city_council_district AS city_council_name,
  v.voter_type,
  -- All participation and vote columns
  v.participation_primary_2016,
  v.participation_primary_2017,
  v.participation_primary_2018,
  v.participation_primary_2019,
  v.participation_primary_2020,
  v.participation_primary_2021,
  v.participation_primary_2022,
  v.participation_primary_2023,
  v.participation_primary_2024,
  v.participation_general_2016,
  v.participation_general_2017,
  v.participation_general_2018,
  v.participation_general_2019,
  v.participation_general_2020,
  v.participation_general_2021,
  v.participation_general_2022,
  v.participation_general_2023,
  v.participation_general_2024,
  v.vote_primary_dem_2016,
  v.vote_primary_rep_2016,
  v.vote_primary_dem_2017,
  v.vote_primary_rep_2017,
  v.vote_primary_dem_2018,
  v.vote_primary_rep_2018,
  v.vote_primary_dem_2019,
  v.vote_primary_rep_2019,
  v.vote_primary_dem_2020,
  v.vote_primary_rep_2020,
  v.vote_primary_dem_2021,
  v.vote_primary_rep_2021,
  v.vote_primary_dem_2022,
  v.vote_primary_rep_2022,
  v.vote_primary_dem_2023,
  v.vote_primary_rep_2023,
  v.vote_primary_dem_2024,
  v.vote_primary_rep_2024,
  -- Geographic columns
  a.latitude,
  a.longitude,
  a.geo_location
FROM `proj-roth.voter_data.voters` v
JOIN `proj-roth.voter_data.individuals` i ON v.master_id = i.master_id
JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id;