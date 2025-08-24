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