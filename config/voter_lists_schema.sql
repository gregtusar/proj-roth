-- Schema for voter_lists table
-- This table stores saved voter lists created by users through queries

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.voter_lists` (
  list_id STRING NOT NULL,  -- UUID for the list
  user_id STRING NOT NULL,  -- User ID from authentication system
  user_email STRING NOT NULL,  -- User email for display/reference
  list_name STRING NOT NULL,  -- Model-generated or user-edited name
  description_text STRING,  -- Original query text that created the list
  sql_query STRING NOT NULL,  -- The actual SQL query to regenerate the list
  row_count INT64,  -- Number of voters in the result
  is_shared BOOL,  -- Whether list is shared with other users
  is_active BOOL,  -- Soft delete flag
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  
  -- Metadata fields
  created_by_model STRING,  -- Which model created this (e.g., 'gemini-1.5-flash')
  query_execution_time_ms INT64,  -- How long the query took to run
  last_accessed_at TIMESTAMP,  -- Track usage
  access_count INT64,  -- Track popularity
  
  -- Additional fields for sharing
  shared_with_emails ARRAY<STRING>,  -- List of emails that can access this list
  share_type STRING,  -- 'private', 'team', 'public'
  
  PRIMARY KEY (list_id) NOT ENFORCED
)
PARTITION BY DATE(created_at)
CLUSTER BY user_id, is_active
OPTIONS(
  description="Stores user-created voter lists from queries",
  labels=[("created_by", "voter_lists_feature"), ("version", "v1")]
);