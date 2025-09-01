#!/usr/bin/env python3
"""
People Data Labs Enrichment Pipeline for NJ Voter Data
Enriches individuals table with additional demographic and social data from PDL API
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from google.cloud import bigquery
from google.cloud import secretmanager
from google.cloud.exceptions import GoogleCloudError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'proj-roth')
DATASET_ID = 'voter_data'
INDIVIDUALS_TABLE = f'{PROJECT_ID}.{DATASET_ID}.individuals'
ENRICHMENT_TABLE = f'{PROJECT_ID}.{DATASET_ID}.pdl_enrichment'

def get_pdl_api_key():
    """Retrieve PDL API key from Secret Manager"""
    # First check environment variable for local development
    api_key = os.getenv('PDL_API_KEY')
    if api_key:
        return api_key.strip()
    
    # Otherwise fetch from Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/pdl-api-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.error(f"Failed to retrieve PDL API key from Secret Manager: {e}")
        return None

PDL_API_KEY = get_pdl_api_key()

# PDL API Configuration
PDL_BASE_URL = 'https://api.peopledatalabs.com/v5/person/enrich'
PDL_BULK_URL = 'https://api.peopledatalabs.com/v5/person/bulk'

@dataclass
class PDLEnrichmentRecord:
    """Data model for PDL enrichment records with full JSON storage"""
    master_id: str
    pdl_data: Dict[str, Any]  # Full PDL response
    likelihood: Optional[float] = None
    pdl_id: Optional[str] = None
    
    # Extracted fields for indexing/querying
    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_job_info: bool = False
    has_education: bool = False
    
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_zip: Optional[str] = None
    
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    
    # Metadata
    enriched_at: datetime = None
    api_version: str = 'v5'
    min_likelihood: Optional[int] = None
    request_params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.enriched_at is None:
            self.enriched_at = datetime.now()
        
        # Extract key fields from pdl_data if available
        if self.pdl_data:
            person = self.pdl_data
            
            # Check what data we have
            self.has_email = bool(person.get('work_email') or person.get('personal_emails'))
            self.has_phone = bool(person.get('mobile_phone') or person.get('phone_numbers'))
            self.has_linkedin = bool(person.get('linkedin_url'))
            self.has_job_info = bool(person.get('job_title') or person.get('job_company_name'))
            self.has_education = bool(person.get('education'))
            
            # Extract location
            self.location_city = person.get('location_city')
            self.location_state = person.get('location_region')
            self.location_zip = person.get('location_postal_code')
            
            # Extract job info
            self.job_title = person.get('job_title')
            self.job_company = person.get('job_company_name')

class PDLEnrichmentPipeline:
    """Pipeline for enriching voter data with People Data Labs API"""
    
    def __init__(self, api_key: str, dry_run: bool = False):
        self.api_key = api_key
        self.dry_run = dry_run
        self.client = bigquery.Client(project=PROJECT_ID)
        self.enrichment_cache = {}
    
    def find_person(self, name: str, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Find individuals by name (fuzzy match) and optionally city"""
        # Parse name into components
        name_parts = name.upper().strip().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
        else:
            # Single name - search both first and last
            first_name = last_name = name_parts[0]
        
        # Build query with fuzzy matching
        query = f"""
        WITH matched_individuals AS (
            SELECT 
                i.master_id,
                i.standardized_name,
                i.name_first,
                i.name_last,
                v.demo_age,
                v.demo_party,
                a.city,
                a.state,
                a.zip_code,
                -- Calculate match score
                CASE 
                    WHEN UPPER(i.name_first) = '{first_name}' AND UPPER(i.name_last) = '{last_name}' THEN 100
                    WHEN UPPER(i.name_first) LIKE '{first_name}%' AND UPPER(i.name_last) = '{last_name}' THEN 90
                    WHEN UPPER(i.name_first) = '{first_name}' AND UPPER(i.name_last) LIKE '{last_name}%' THEN 85
                    WHEN SOUNDEX(i.name_first) = SOUNDEX('{first_name}') AND UPPER(i.name_last) = '{last_name}' THEN 80
                    WHEN UPPER(i.name_first) = '{first_name}' AND SOUNDEX(i.name_last) = SOUNDEX('{last_name}') THEN 75
                    WHEN UPPER(i.name_first) LIKE '{first_name}%' AND UPPER(i.name_last) LIKE '{last_name}%' THEN 70
                    ELSE 50
                END as match_score
            FROM `{INDIVIDUALS_TABLE}` i
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.voters` v ON i.master_id = v.master_id
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individual_addresses` ia ON i.master_id = ia.master_id
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a ON ia.address_id = a.address_id
            WHERE (
                UPPER(i.name_first) LIKE '{first_name}%' 
                OR UPPER(i.name_last) LIKE '{last_name}%'
                OR SOUNDEX(i.name_first) = SOUNDEX('{first_name}')
                OR SOUNDEX(i.name_last) = SOUNDEX('{last_name}')
            )
        """
        
        if city:
            query += f" AND UPPER(a.city) = '{city.upper()}'"
        
        query += f"""
        )
        SELECT * FROM matched_individuals
        ORDER BY match_score DESC, standardized_name
        LIMIT {limit}
        """
        
        logger.info(f"Searching for '{name}'" + (f" in {city}" if city else ""))
        results = self.client.query(query).result()
        matches = [dict(row) for row in results]
        
        if matches:
            logger.info(f"Found {len(matches)} potential matches:")
            for i, match in enumerate(matches, 1):
                logger.info(f"  {i}. {match['standardized_name']} - {match.get('city', 'N/A')}, "
                          f"Age: {match.get('demo_age', 'N/A')}, Party: {match.get('demo_party', 'N/A')}, "
                          f"Score: {match['match_score']}")
        else:
            logger.info("No matches found")
        
        return matches
    
    def enrich_by_master_id(self, master_id: str, min_likelihood: int = 8) -> Optional[PDLEnrichmentRecord]:
        """Enrich a specific individual by master_id"""
        # Get individual details with all available fields
        query = f"""
        SELECT 
            i.master_id,
            i.standardized_name,
            i.name_first,
            i.name_middle,
            i.name_last,
            v.demo_age,
            v.email,
            v.phone_1,
            a.street_number,
            a.street_name,
            a.street_suffix,
            a.city,
            a.state,
            a.zip_code,
            a.standardized_address
        FROM `{INDIVIDUALS_TABLE}` i
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.voters` v ON i.master_id = v.master_id
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individual_addresses` ia ON i.master_id = ia.master_id
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a ON ia.address_id = a.address_id
        WHERE i.master_id = '{master_id}'
        """
        
        results = list(self.client.query(query).result())
        if not results:
            logger.error(f"No individual found with master_id: {master_id}")
            return None
        
        individual = dict(results[0])
        logger.info(f"Enriching: {individual['standardized_name']} (master_id: {master_id})")
        
        return self.enrich_individual(individual, min_likelihood=min_likelihood)
        
    def create_enrichment_table(self):
        """Create the PDL enrichment table if it doesn't exist"""
        # Table is now created via SQL script with JSON schema
        # This method just checks if table exists
        try:
            self.client.get_table(ENRICHMENT_TABLE)
            logger.info(f"Table {ENRICHMENT_TABLE} already exists")
        except Exception:
            logger.error(f"Table {ENRICHMENT_TABLE} does not exist. Please run: bq query --use_legacy_sql=false < scripts/update_pdl_enrichment_json_schema.sql")
            raise
    
    def get_unenriched_individuals(self, limit: int = 100) -> List[Dict]:
        """Get individuals that haven't been enriched yet"""
        query = f"""
        SELECT 
            i.master_id,
            i.standardized_name,
            i.name_first,
            i.name_middle,
            i.name_last,
            v.demo_age,
            v.email,
            v.phone_1,
            a.street_number,
            a.street_name,
            a.street_suffix,
            a.city,
            a.state,
            a.zip_code,
            a.standardized_address
        FROM `{INDIVIDUALS_TABLE}` i
        LEFT JOIN `{ENRICHMENT_TABLE}` e ON i.master_id = e.master_id
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.voters` v ON i.master_id = v.master_id
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.individual_addresses` ia ON i.master_id = ia.master_id
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.addresses` a ON ia.address_id = a.address_id
        WHERE e.master_id IS NULL
        AND i.name_first IS NOT NULL
        AND i.name_last IS NOT NULL
        LIMIT {limit}
        """
        
        logger.info(f"Fetching up to {limit} unenriched individuals")
        results = self.client.query(query).result()
        individuals = [dict(row) for row in results]
        logger.info(f"Found {len(individuals)} individuals to enrich")
        return individuals
    
    def enrich_individual(self, individual: Dict, min_likelihood: int = 8) -> Optional[PDLEnrichmentRecord]:
        """Enrich a single individual using PDL API
        
        Args:
            individual: Dict with person data
            min_likelihood: Minimum confidence score (1-10, default 6)
                1-3: Very loose matching, many false positives
                4-6: Balanced matching
                7-8: Strict matching (our default to control costs)
                7-9: Strict matching, may miss valid matches
                10: Exact match only
        """
        
        # Build PDL query parameters
        params = {
            'api_key': self.api_key,
            'pretty': False,
            'min_likelihood': min_likelihood
        }
        
        # Add name - include middle name if available
        if individual.get('name_first') and individual.get('name_last'):
            if individual.get('name_middle'):
                params['name'] = f"{individual['name_first']} {individual['name_middle']} {individual['name_last']}"
            else:
                params['name'] = f"{individual['name_first']} {individual['name_last']}"
        
        # Add email if available (strong identifier)
        if individual.get('email'):
            params['email'] = individual['email']
        
        # Add phone if available (strong identifier)
        if individual.get('phone_1'):
            # Clean phone number - remove non-digits
            phone = ''.join(filter(str.isdigit, str(individual['phone_1'])))
            if len(phone) >= 10:
                params['phone'] = phone
        
        # Add location - more specific is better
        if individual.get('street_number') and individual.get('street_name'):
            # Use street address for most precise matching
            street = f"{individual['street_number']} {individual['street_name']}"
            if individual.get('street_suffix'):
                street += f" {individual['street_suffix']}"
            params['street_address'] = street
        
        if individual.get('city'):
            params['locality'] = individual['city']
        
        if individual.get('state'):
            params['region'] = individual['state']
        
        if individual.get('zip_code'):
            params['postal_code'] = individual['zip_code']
        
        # Add birth date if we can derive it from age
        if individual.get('demo_age'):
            # Approximate birth year
            import datetime
            current_year = datetime.datetime.now().year
            birth_year = current_year - int(individual['demo_age'])
            params['birth_date'] = str(birth_year)
        
        # Log matching parameters for debugging
        logger.debug(f"PDL matching parameters for {individual['master_id']}:")
        for key, value in params.items():
            if key != 'api_key':
                logger.debug(f"  {key}: {value}")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would enrich {individual['master_id']} with params: {params}")
            return None
        
        try:
            response = requests.get(PDL_BASE_URL, params=params, timeout=10)
            data = response.json()  # Get JSON even for error responses
            
            if data.get('status') == 200 and data.get('data'):
                person = data['data']
                
                # Store request params (minus API key)
                request_params_clean = {k: v for k, v in params.items() if k != 'api_key'}
                
                # Create record with full JSON data
                record = PDLEnrichmentRecord(
                    master_id=individual['master_id'],
                    pdl_data=person,  # Store complete PDL response
                    likelihood=data.get('likelihood'),
                    pdl_id=person.get('id'),
                    min_likelihood=min_likelihood,
                    request_params=request_params_clean
                )
                
                logger.info(f"Successfully enriched {individual['master_id']} (likelihood: {data.get('likelihood')})")
                return record
            else:
                # Check if there was a match below threshold
                if data.get('status') == 404:
                    logger.info(f"No match found for {individual['master_id']} at min_likelihood={min_likelihood}")
                else:
                    logger.debug(f"No match found for {individual['master_id']}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"API error enriching {individual['master_id']}: {e}")
            return None
    
    def save_enrichment_batch(self, records: List[PDLEnrichmentRecord]):
        """Save enrichment records to BigQuery"""
        if not records:
            return
        
        rows_to_insert = []
        for record in records:
            row = {
                'master_id': record.master_id,
                'pdl_id': record.pdl_id,
                'likelihood': record.likelihood,
                'pdl_data': json.dumps(record.pdl_data),  # Store as JSON string
                'has_email': record.has_email,
                'has_phone': record.has_phone,
                'has_linkedin': record.has_linkedin,
                'has_job_info': record.has_job_info,
                'has_education': record.has_education,
                'location_city': record.location_city,
                'location_state': record.location_state,
                'location_zip': record.location_zip,
                'job_title': record.job_title,
                'job_company': record.job_company,
                'enriched_at': record.enriched_at.isoformat() if record.enriched_at else None,
                'api_version': record.api_version,
                'min_likelihood': record.min_likelihood,
                'request_params': json.dumps(record.request_params) if record.request_params else None
            }
            
            rows_to_insert.append(row)
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(rows_to_insert)} records to BigQuery")
        else:
            table = self.client.get_table(ENRICHMENT_TABLE)
            errors = self.client.insert_rows_json(table, rows_to_insert)
            
            if errors:
                logger.error(f"Failed to insert rows: {errors}")
            else:
                logger.info(f"Successfully inserted {len(rows_to_insert)} enrichment records")
    
    def run_enrichment(self, batch_size: int = 100, total_limit: int = 1000):
        """Run the enrichment pipeline"""
        logger.info(f"Starting enrichment pipeline (batch_size={batch_size}, limit={total_limit})")
        
        # Create table if needed
        self.create_enrichment_table()
        
        total_enriched = 0
        total_attempted = 0
        
        while total_attempted < total_limit:
            # Get batch of unenriched individuals
            individuals = self.get_unenriched_individuals(limit=min(batch_size, total_limit - total_attempted))
            
            if not individuals:
                logger.info("No more individuals to enrich")
                break
            
            enrichment_records = []
            
            for individual in individuals:
                # Rate limiting - PDL has rate limits we need to respect
                time.sleep(0.1)  # 10 requests per second max
                
                record = self.enrich_individual(individual)
                if record:
                    enrichment_records.append(record)
                    total_enriched += 1
                
                total_attempted += 1
                
                # Save batch periodically
                if len(enrichment_records) >= 10:
                    self.save_enrichment_batch(enrichment_records)
                    enrichment_records = []
            
            # Save remaining records
            if enrichment_records:
                self.save_enrichment_batch(enrichment_records)
        
        logger.info(f"Enrichment complete: {total_enriched}/{total_attempted} successfully enriched")
        return total_enriched, total_attempted

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich voter data with People Data Labs')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Batch enrichment command (default)
    batch_parser = subparsers.add_parser('batch', help='Batch enrichment of unenriched individuals')
    batch_parser.add_argument('--dry-run', action='store_true', help='Run without making API calls or DB changes')
    batch_parser.add_argument('--batch-size', type=int, default=10, help='Number of records per batch')
    batch_parser.add_argument('--limit', type=int, default=100, help='Total number of records to process')
    batch_parser.add_argument('--api-key', help='PDL API key (or set PDL_API_KEY env var)')
    
    # Person lookup command
    person_parser = subparsers.add_parser('person', help='Look up and enrich a specific person')
    person_parser.add_argument('name', help='Person name to search for (e.g., "John Smith")')
    person_parser.add_argument('--city', help='Optional city to narrow search (e.g., "Summit")')
    person_parser.add_argument('--dry-run', action='store_true', help='Run without making API calls or DB changes')
    person_parser.add_argument('--api-key', help='PDL API key (or set PDL_API_KEY env var)')
    person_parser.add_argument('--select', type=int, help='Automatically select match number (1-based) without prompting')
    person_parser.add_argument('--min-likelihood', type=int, default=8, choices=range(1,11), 
                              help='Minimum match confidence (1-10, default 8). Higher = stricter matching')
    person_parser.add_argument('--debug', action='store_true', help='Show detailed matching information')
    
    # Master ID enrichment command
    master_parser = subparsers.add_parser('master-id', help='Enrich a specific master_id')
    master_parser.add_argument('master_id', help='Master ID to enrich')
    master_parser.add_argument('--dry-run', action='store_true', help='Run without making API calls or DB changes')
    master_parser.add_argument('--api-key', help='PDL API key (or set PDL_API_KEY env var)')
    master_parser.add_argument('--min-likelihood', type=int, default=8, choices=range(1,11),
                              help='Minimum match confidence (1-10, default 8). Higher = stricter matching')
    master_parser.add_argument('--debug', action='store_true', help='Show detailed matching information')
    
    args = parser.parse_args()
    
    # Default to batch if no command specified
    if not args.command:
        args.command = 'batch'
        args.dry_run = False
        args.batch_size = 10
        args.limit = 100
        args.api_key = None
    
    api_key = args.api_key if hasattr(args, 'api_key') else None
    api_key = api_key or PDL_API_KEY
    
    if not api_key and not args.dry_run:
        logger.error("PDL API key required. Key should be in Secret Manager as 'pdl-api-key' or set PDL_API_KEY env var")
        return 1
    
    pipeline = PDLEnrichmentPipeline(api_key=api_key, dry_run=args.dry_run)
    
    if args.command == 'batch':
        # Create table if needed
        pipeline.create_enrichment_table()
        enriched, attempted = pipeline.run_enrichment(
            batch_size=args.batch_size,
            total_limit=args.limit
        )
        print(f"\nResults: {enriched}/{attempted} records enriched")
        
    elif args.command == 'person':
        # Find person by name
        matches = pipeline.find_person(args.name, args.city)
        
        if not matches:
            print("No matches found")
            return 1
        
        # Select which match to enrich
        if args.select:
            if args.select < 1 or args.select > len(matches):
                print(f"Invalid selection: {args.select}. Must be between 1 and {len(matches)}")
                return 1
            selected_idx = args.select - 1
        else:
            # Interactive selection
            print("\nSelect person to enrich (enter number):")
            for i, match in enumerate(matches, 1):
                print(f"  {i}. {match['standardized_name']} - {match.get('city', 'N/A')}, "
                      f"Age: {match.get('demo_age', 'N/A')}, Party: {match.get('demo_party', 'N/A')}")
            
            try:
                selection = input("\nEnter selection (1-{}): ".format(len(matches)))
                selected_idx = int(selection) - 1
                if selected_idx < 0 or selected_idx >= len(matches):
                    print("Invalid selection")
                    return 1
            except (ValueError, KeyboardInterrupt):
                print("\nCancelled")
                return 1
        
        selected = matches[selected_idx]
        print(f"\nEnriching: {selected['standardized_name']} (master_id: {selected['master_id']})")
        
        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Create table if needed
        pipeline.create_enrichment_table()
        
        # Enrich the selected person with specified confidence level
        record = pipeline.enrich_by_master_id(selected['master_id'], min_likelihood=args.min_likelihood)
        if record:
            pipeline.save_enrichment_batch([record])
            print(f"Successfully enriched {selected['standardized_name']}")
            
            # Display some results from the full JSON
            print("\nEnrichment data:")
            person = record.pdl_data
            if person.get('job_title'):
                print(f"  Job: {person.get('job_title')} at {person.get('job_company_name')}")
            if person.get('education') and len(person['education']) > 0:
                school = person['education'][0].get('school', {}).get('name')
                if school:
                    print(f"  Education: {school}")
            if person.get('linkedin_url'):
                print(f"  LinkedIn: {person.get('linkedin_url')}")
            if person.get('interests'):
                print(f"  Interests: {', '.join(person['interests'][:5])}")
            if person.get('skills'):
                print(f"  Skills: {', '.join(person['skills'][:5])}")
        else:
            print("No enrichment data found")
            
    elif args.command == 'master-id':
        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Create table if needed
        pipeline.create_enrichment_table()
        
        # Enrich specific master_id with specified confidence level
        record = pipeline.enrich_by_master_id(args.master_id, min_likelihood=args.min_likelihood)
        if record:
            pipeline.save_enrichment_batch([record])
            print(f"Successfully enriched master_id: {args.master_id}")
            
            # Display some results from the full JSON
            print("\nEnrichment data:")
            person = record.pdl_data
            if person.get('job_title'):
                print(f"  Job: {person.get('job_title')} at {person.get('job_company_name')}") 
            if person.get('education') and len(person['education']) > 0:
                school = person['education'][0].get('school', {}).get('name')
                if school:
                    print(f"  Education: {school}")
            if person.get('linkedin_url'):
                print(f"  LinkedIn: {person.get('linkedin_url')}")
            if person.get('skills'):
                print(f"  Skills: {', '.join(person['skills'][:5])}")
        else:
            print(f"No enrichment data found for master_id: {args.master_id}")
    
    return 0

if __name__ == '__main__':
    exit(main())