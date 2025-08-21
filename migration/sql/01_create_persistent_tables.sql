-- Create persistent tables that will never be dropped
-- These tables preserve expensive geocoding data and entity resolution

-- 1. Individuals table - unique people based on name matching
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.individuals` (
  master_id STRING NOT NULL,
  standardized_name STRING NOT NULL,
  name_first STRING,
  name_middle STRING,
  name_last STRING,
  name_suffix STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY master_id;

-- Add primary key constraint
ALTER TABLE `proj-roth.voter_data.individuals`
ADD PRIMARY KEY (master_id) NOT ENFORCED;

-- 2. Addresses table - unique normalized addresses with geocoding
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.addresses` (
  address_id STRING NOT NULL,
  standardized_address STRING NOT NULL,
  street_number STRING,
  street_name STRING,
  street_suffix STRING,
  city STRING,
  state STRING,
  zip_code STRING,
  county STRING,
  geo_location GEOGRAPHY,
  latitude FLOAT64,
  longitude FLOAT64,
  geocoding_source STRING,
  geocoding_date DATE,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY address_id, county;

-- Add primary key constraint
ALTER TABLE `proj-roth.voter_data.addresses`
ADD PRIMARY KEY (address_id) NOT ENFORCED;

-- Create index on standardized address for lookups
CREATE SEARCH INDEX address_search_idx
ON `proj-roth.voter_data.addresses`(standardized_address);

-- 3. Individual-Address junction table
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.individual_addresses` (
  individual_address_id STRING NOT NULL,
  master_id STRING NOT NULL,
  address_id STRING NOT NULL,
  address_type STRING DEFAULT 'residential',
  valid_from DATE DEFAULT CURRENT_DATE(),
  valid_to DATE,
  is_current BOOLEAN DEFAULT TRUE,
  source_system STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY master_id, address_id;

-- Add primary key and foreign key constraints
ALTER TABLE `proj-roth.voter_data.individual_addresses`
ADD PRIMARY KEY (individual_address_id) NOT ENFORCED;

ALTER TABLE `proj-roth.voter_data.individual_addresses`
ADD CONSTRAINT fk_individual
FOREIGN KEY (master_id) REFERENCES `proj-roth.voter_data.individuals`(master_id) NOT ENFORCED;

ALTER TABLE `proj-roth.voter_data.individual_addresses`
ADD CONSTRAINT fk_address
FOREIGN KEY (address_id) REFERENCES `proj-roth.voter_data.addresses`(address_id) NOT ENFORCED;