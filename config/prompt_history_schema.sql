-- Schema for storing all user prompts and agent responses
-- This table captures the full conversation history for analysis and auditing

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.prompt_history` (
  prompt_id STRING NOT NULL,
  user_id STRING NOT NULL,
  user_email STRING NOT NULL,
  session_id STRING,
  prompt_text STRING NOT NULL,
  response_text STRING,
  advisor_persona STRING, -- Which advisor responded (Elon, Zohran, Susie, Tara, Jen)
  tools_used ARRAY<STRING>, -- List of tools used (bigquery_select, geocode_address, etc.)
  sql_queries ARRAY<STRING>, -- Any SQL queries executed
  row_count INTEGER, -- Number of rows returned if query was run
  error_message STRING, -- Any errors encountered
  prompt_timestamp TIMESTAMP NOT NULL,
  response_timestamp TIMESTAMP,
  response_time_ms INTEGER, -- Time taken to generate response in milliseconds
  client_type STRING, -- 'streamlit', 'cli', 'react', etc.
  ip_address STRING,
  user_agent STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(prompt_timestamp)
CLUSTER BY user_id, user_email, prompt_timestamp;

-- Note: BigQuery uses clustering instead of traditional indexes
-- The table is already clustered by user_id, user_email for fast lookups

-- Create a view for easy analysis of prompt patterns
CREATE OR REPLACE VIEW `proj-roth.voter_data.prompt_analytics` AS
SELECT 
  DATE(prompt_timestamp) as prompt_date,
  user_email,
  COUNT(*) as prompt_count,
  COUNT(DISTINCT session_id) as session_count,
  AVG(response_time_ms) as avg_response_time_ms,
  COUNT(error_message) as error_count,
  ARRAY_AGG(DISTINCT advisor_persona IGNORE NULLS) as advisors_used,
  COUNT(CASE WHEN ARRAY_LENGTH(sql_queries) > 0 THEN 1 END) as queries_executed,
  COUNT(CASE WHEN ARRAY_LENGTH(tools_used) > 0 THEN 1 END) as prompts_with_tools
FROM `proj-roth.voter_data.prompt_history`
GROUP BY prompt_date, user_email
ORDER BY prompt_date DESC, prompt_count DESC;