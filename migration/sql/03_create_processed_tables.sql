-- Create processed tables that link raw data to individuals
-- These tables are regenerated when raw data is updated

-- 1. Voters table - links raw_voters to individuals
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.voters` (
  voter_record_id STRING NOT NULL,
  vendor_voter_id STRING NOT NULL,
  master_id STRING NOT NULL,
  address_id STRING NOT NULL,
  -- Demographics
  demo_party STRING,
  demo_age INT64,
  demo_race STRING,
  demo_race_confidence STRING,
  demo_gender STRING,
  -- Registration
  registration_status STRING,
  voter_type STRING,
  -- Geographic/Political Districts
  congressional_district STRING,
  state_house_district STRING,
  state_senate_district STRING,
  precinct STRING,
  municipal_name STRING,
  county_name STRING,
  city_council_district STRING,
  -- Scores
  score_support_generic_dem FLOAT64,
  current_support_score FLOAT64,
  -- Voting History (2016-2024)
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
  -- Primary votes by party
  vote_primary_dem_2016 BOOLEAN,
  vote_primary_rep_2016 BOOLEAN,
  vote_primary_dem_2017 BOOLEAN,
  vote_primary_rep_2017 BOOLEAN,
  vote_primary_dem_2018 BOOLEAN,
  vote_primary_rep_2018 BOOLEAN,
  vote_primary_dem_2019 BOOLEAN,
  vote_primary_rep_2019 BOOLEAN,
  vote_primary_dem_2020 BOOLEAN,
  vote_primary_rep_2020 BOOLEAN,
  vote_primary_dem_2021 BOOLEAN,
  vote_primary_rep_2021 BOOLEAN,
  vote_primary_dem_2022 BOOLEAN,
  vote_primary_rep_2022 BOOLEAN,
  vote_primary_dem_2023 BOOLEAN,
  vote_primary_rep_2023 BOOLEAN,
  vote_primary_dem_2024 BOOLEAN,
  vote_primary_rep_2024 BOOLEAN,
  -- Contact info (optional)
  email STRING,
  phone_1 STRING,
  phone_2 STRING,
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY county_name, demo_party, master_id;

-- 2. Donations table - links raw_donations to individuals
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.donations` (
  donation_record_id STRING NOT NULL,
  master_id STRING,  -- NULL if no match found
  address_id STRING, -- NULL if no match found
  -- Donation details
  committee_name STRING,
  contribution_amount NUMERIC,
  election_type STRING,
  election_year INT64,
  employer STRING,
  occupation STRING,
  donation_date DATE,
  -- Original name from raw data (for unmatched records)
  original_full_name STRING,
  original_address STRING,
  -- Match confidence
  match_confidence FLOAT64,
  match_method STRING,
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY master_id, election_year;