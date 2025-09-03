#!/usr/bin/env python3
"""
People Data Labs (PDL) enrichment tool for the NJ Voter Chat agent.
Provides ability to fetch existing enrichment data or trigger new enrichment on-demand.
"""

import json
import logging
import os
import sys
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud import secretmanager

# PDL enrichment classes defined inline to avoid import issues
class PDLEnrichmentRecord:
    """Placeholder class for PDL enrichment record"""
    pass

class PDLEnrichmentPipeline:
    """Placeholder class for PDL enrichment pipeline"""
    pass

logger = logging.getLogger(__name__)

class PDLEnrichmentTool:
    """Tool for fetching and triggering PDL enrichment data"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'proj-roth')
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_id = 'voter_data'
        self.enrichment_table = f'{self.project_id}.{self.dataset_id}.pdl_enrichment'
        self.individuals_table = f'{self.project_id}.{self.dataset_id}.individuals'
        
        # Cost control settings
        self.cost_per_enrichment = 0.25  # USD
        self.daily_budget_limit = 10.00  # USD
        self.require_confirmation_above = 5.00  # USD cumulative in session
        
        # Track session costs
        self.session_cost = 0.0
        self.session_enrichments = []
        
        # Initialize pipeline (lazy load API key)
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Lazy load the enrichment pipeline with API key"""
        if self._pipeline is None:
            api_key = self._get_pdl_api_key()
            if not api_key:
                raise ValueError("PDL API key not found in Secret Manager (secret: pdl-api-key)")
            self._pipeline = PDLEnrichmentPipeline(api_key=api_key, dry_run=False)
        return self._pipeline
    
    def _get_pdl_api_key(self):
        """Retrieve PDL API key from Secret Manager only"""
        # Always use Secret Manager for consistency and security
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/pdl-api-key/versions/latest"
            response = client.access_secret_version(request={"name": name})
            api_key = response.payload.data.decode("UTF-8").strip()
            logger.info("Successfully retrieved PDL API key from Secret Manager")
            return api_key
        except Exception as e:
            logger.error(f"Failed to retrieve PDL API key from Secret Manager: {e}")
            return None
    
    def get_enrichment(self, master_id: str) -> Dict[str, Any]:
        """
        Fetch existing PDL enrichment data for a master_id.
        
        Args:
            master_id: The voter's master_id
            
        Returns:
            Dict containing enrichment data or status
        """
        try:
            # Check if enrichment exists
            query = f"""
            SELECT 
                e.master_id,
                e.pdl_id,
                e.likelihood,
                e.pdl_data,
                e.enriched_at,
                e.has_email,
                e.has_phone,
                e.has_linkedin,
                e.has_job_info,
                e.has_education,
                i.standardized_name,
                v.demo_age,
                v.demo_party,
                a.city,
                a.state
            FROM `{self.enrichment_table}` e
            JOIN `{self.individuals_table}` i ON e.master_id = i.master_id
            LEFT JOIN `{self.project_id}.{self.dataset_id}.voters` v ON i.master_id = v.master_id
            LEFT JOIN `{self.project_id}.{self.dataset_id}.individual_addresses` ia ON i.master_id = ia.master_id
            LEFT JOIN `{self.project_id}.{self.dataset_id}.addresses` a ON ia.address_id = a.address_id
            WHERE e.master_id = @master_id
            ORDER BY e.enriched_at DESC
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("master_id", "STRING", master_id)
                ]
            )
            
            results = list(self.client.query(query, job_config=job_config).result())
            
            if results:
                row = dict(results[0])
                
                # Parse the JSON data (handle both string and dict)
                if isinstance(row['pdl_data'], str):
                    pdl_data = json.loads(row['pdl_data']) if row['pdl_data'] else {}
                else:
                    pdl_data = row['pdl_data'] if row['pdl_data'] else {}
                
                # Calculate age of enrichment
                enriched_at = row['enriched_at']
                age_days = (datetime.now(enriched_at.tzinfo) - enriched_at).days
                
                return {
                    'status': 'found',
                    'master_id': master_id,
                    'name': row['standardized_name'],
                    'location': f"{row.get('city', '')}, {row.get('state', '')}",
                    'age': row.get('demo_age'),
                    'party': row.get('demo_party'),
                    'enrichment': {
                        'pdl_id': row['pdl_id'],
                        'likelihood': row['likelihood'],
                        'enriched_at': enriched_at.isoformat(),
                        'age_days': age_days,
                        'has_email': row['has_email'],
                        'has_phone': row['has_phone'],
                        'has_linkedin': row['has_linkedin'],
                        'has_job_info': row['has_job_info'],
                        'has_education': row['has_education'],
                        'data': pdl_data
                    }
                }
            else:
                # Check if the master_id exists at all
                check_query = f"""
                SELECT 
                    i.standardized_name,
                    v.demo_age,
                    v.demo_party,
                    a.city,
                    a.state
                FROM `{self.individuals_table}` i
                LEFT JOIN `{self.project_id}.{self.dataset_id}.voters` v ON i.master_id = v.master_id
                LEFT JOIN `{self.project_id}.{self.dataset_id}.individual_addresses` ia ON i.master_id = ia.master_id
                LEFT JOIN `{self.project_id}.{self.dataset_id}.addresses` a ON ia.address_id = a.address_id
                WHERE i.master_id = @master_id
                """
                
                check_results = list(self.client.query(check_query, job_config=job_config).result())
                
                if check_results:
                    row = dict(check_results[0])
                    return {
                        'status': 'not_enriched',
                        'master_id': master_id,
                        'name': row['standardized_name'],
                        'location': f"{row.get('city', '')}, {row.get('state', '')}",
                        'age': row.get('demo_age'),
                        'party': row.get('demo_party'),
                        'message': 'No PDL enrichment data found for this individual. Use trigger_enrichment to enrich.'
                    }
                else:
                    return {
                        'status': 'not_found',
                        'master_id': master_id,
                        'message': f'No individual found with master_id: {master_id}'
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching enrichment for {master_id}: {e}")
            return {
                'status': 'error',
                'master_id': master_id,
                'error': str(e)
            }
    
    def trigger_enrichment(self, master_id: str, min_likelihood: int = 8, 
                          skip_if_exists: bool = True, 
                          require_confirmation: bool = True) -> Dict[str, Any]:
        """
        Trigger PDL enrichment for a specific master_id.
        
        Args:
            master_id: The voter's master_id to enrich
            min_likelihood: Minimum PDL confidence (1-10, default 6)
            skip_if_exists: Skip if enrichment already exists (default True)
            require_confirmation: Require confirmation for high costs (default True)
            
        Returns:
            Dict containing enrichment result or status
        """
        try:
            # First check if enrichment already exists
            if skip_if_exists:
                existing = self.get_enrichment(master_id)
                if existing['status'] == 'found':
                    age_days = existing['enrichment']['age_days']
                    if age_days < 180:  # Less than 6 months old
                        return {
                            'status': 'already_enriched',
                            'master_id': master_id,
                            'message': f'Already enriched {age_days} days ago',
                            'enrichment': existing['enrichment']
                        }
            
            # Check if master_id exists
            existing = self.get_enrichment(master_id)
            if existing['status'] == 'not_found':
                return existing
            
            # Cost control checks
            if require_confirmation:
                # Check daily spend
                daily_spent = self._get_daily_spend()
                if daily_spent + self.cost_per_enrichment > self.daily_budget_limit:
                    return {
                        'status': 'budget_exceeded',
                        'master_id': master_id,
                        'message': f'Daily budget limit (${self.daily_budget_limit}) would be exceeded. '
                                  f'Already spent ${daily_spent:.2f} today.',
                        'action_required': 'Increase daily budget or wait until tomorrow'
                    }
                
                # Check session spend
                if self.session_cost + self.cost_per_enrichment > self.require_confirmation_above:
                    return {
                        'status': 'confirmation_required',
                        'master_id': master_id,
                        'message': f'Session cost (${self.session_cost + self.cost_per_enrichment:.2f}) '
                                  f'exceeds confirmation threshold (${self.require_confirmation_above})',
                        'voter_info': {
                            'name': existing.get('name'),
                            'location': existing.get('location'),
                            'age': existing.get('age'),
                            'party': existing.get('party')
                        },
                        'cost': self.cost_per_enrichment,
                        'action_required': 'Confirm enrichment or adjust threshold'
                    }
            
            # Perform enrichment
            logger.info(f"Triggering PDL enrichment for {master_id} (cost: ${self.cost_per_enrichment})")
            
            record = self.pipeline.enrich_by_master_id(master_id, min_likelihood=min_likelihood)
            
            if record:
                # Save to BigQuery
                self.pipeline.save_enrichment_batch([record])
                
                # Update session tracking
                self.session_cost += self.cost_per_enrichment
                self.session_enrichments.append({
                    'master_id': master_id,
                    'name': existing.get('name'),
                    'cost': self.cost_per_enrichment,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Return enriched data
                return {
                    'status': 'enriched',
                    'master_id': master_id,
                    'name': existing.get('name'),
                    'location': existing.get('location'),
                    'cost': self.cost_per_enrichment,
                    'session_total_cost': self.session_cost,
                    'enrichment': {
                        'pdl_id': record.pdl_id,
                        'likelihood': record.likelihood,
                        'has_email': record.has_email,
                        'has_phone': record.has_phone,
                        'has_linkedin': record.has_linkedin,
                        'has_job_info': record.has_job_info,
                        'has_education': record.has_education,
                        'data': record.pdl_data
                    }
                }
            else:
                return {
                    'status': 'no_match',
                    'master_id': master_id,
                    'name': existing.get('name'),
                    'message': f'No PDL match found at min_likelihood={min_likelihood}',
                    'suggestion': 'Try lowering min_likelihood parameter (current: {min_likelihood}, try: 4)'
                }
                
        except Exception as e:
            logger.error(f"Error triggering enrichment for {master_id}: {e}")
            return {
                'status': 'error',
                'master_id': master_id,
                'error': str(e)
            }
    
    def _get_daily_spend(self) -> float:
        """Calculate how much has been spent on enrichments today"""
        query = f"""
        SELECT COUNT(*) as enrichment_count
        FROM `{self.enrichment_table}`
        WHERE DATE(enriched_at) = CURRENT_DATE()
        """
        
        results = list(self.client.query(query).result())
        if results:
            count = results[0]['enrichment_count']
            return count * self.cost_per_enrichment
        return 0.0
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of enrichments performed in this session"""
        return {
            'session_cost': self.session_cost,
            'enrichment_count': len(self.session_enrichments),
            'enrichments': self.session_enrichments,
            'daily_spend': self._get_daily_spend(),
            'daily_budget_remaining': self.daily_budget_limit - self._get_daily_spend()
        }


def pdl_enrichment_tool(master_id: str, action: str = "fetch", 
                        min_likelihood: int = 8,
                        force: bool = False) -> Dict[str, Any]:
    """
    ADK tool function for PDL enrichment.
    
    Args:
        master_id: The voter's master_id
        action: Either "fetch" (get existing data) or "enrich" (trigger new enrichment)
        min_likelihood: For enrichment, minimum PDL confidence (1-10, default 8)
        force: For enrichment, skip cost confirmations and existing data checks
        
    Returns:
        Dict with enrichment data or status information
    """
    tool = PDLEnrichmentTool()
    
    if action == "fetch":
        return tool.get_enrichment(master_id)
    elif action == "enrich":
        return tool.trigger_enrichment(
            master_id, 
            min_likelihood=min_likelihood,
            skip_if_exists=not force,
            require_confirmation=not force
        )
    elif action == "session_summary":
        return tool.get_session_summary()
    else:
        return {
            'status': 'error',
            'message': f'Invalid action: {action}. Use "fetch" or "enrich"'
        }


if __name__ == "__main__":
    # Test the tool
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdl_tool.py <master_id> [fetch|enrich] [min_likelihood]")
        sys.exit(1)
    
    master_id = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "fetch"
    min_likelihood = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    
    result = pdl_enrichment_tool(master_id, action, min_likelihood)
    print(json.dumps(result, indent=2, default=str))