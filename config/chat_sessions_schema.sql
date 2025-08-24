-- Schema for chat sessions table
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.chat_sessions` (
  session_id STRING NOT NULL,
  user_id STRING NOT NULL,
  user_email STRING NOT NULL,
  session_name STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  message_count INTEGER DEFAULT 0,
  metadata JSON
);

-- Schema for chat messages table
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.chat_messages` (
  message_id STRING NOT NULL,
  session_id STRING NOT NULL,
  user_id STRING NOT NULL,
  message_type STRING NOT NULL, -- 'user' or 'assistant'
  message_text STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  sequence_number INTEGER NOT NULL,
  metadata JSON
);

-- Create indexes for performance
-- Note: BigQuery doesn't support traditional indexes, but we can create clustered tables
-- These would need to be created with the table definition

-- For querying sessions by user
-- CLUSTER BY user_id, created_at

-- For querying messages by session
-- CLUSTER BY session_id, sequence_number