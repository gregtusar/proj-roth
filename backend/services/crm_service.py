"""CRM service for managing voter profiles and events."""
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.cloud import bigquery
from google.cloud import firestore

from core.config import get_settings
from services.bigquery_service_class import BigQueryService
from services.voter_index_service import VoterIndexService

logger = logging.getLogger(__name__)


class CRMService:
    """Service for CRM operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.bq_service = BigQueryService()
        self.firestore_client = firestore.Client(project=self.settings.GOOGLE_CLOUD_PROJECT)
        self.events_collection = "events"
        self.voter_index = VoterIndexService()
        
    async def search_voters(
        self, 
        query: str, 
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for voters with typeahead functionality using indexed trie.
        Supports progressive search as user types.
        """
        try:
            # First try to use the indexed search for speed
            results = await self.voter_index.search(query, limit)
            
            if results:
                return results
            
            # Fallback to direct BigQuery search if index is not available
            logger.warning("Using fallback BigQuery search - index may not be initialized")
            
            # Parse the query - could be "last, first" or just partial name
            query_parts = [p.strip().upper() for p in query.split(',')]
            
            if len(query_parts) == 2:
                # Format: "last, first"
                last_name = query_parts[0]
                first_name = query_parts[1]
                sql_query = f"""
                SELECT DISTINCT
                    v.master_id,
                    i.name_last,
                    i.name_first,
                    i.name_middle,
                    a.standardized_address as addr_residential_line1,
                    a.city as addr_residential_city,
                    a.state as addr_residential_state,
                    a.zip_code as addr_residential_zip,
                    v.demo_age,
                    v.demo_party
                FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters` v
                JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.individuals` i
                    ON v.master_id = i.master_id
                LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.addresses` a
                    ON v.address_id = a.address_id
                WHERE UPPER(i.name_last) LIKE '{last_name}%'
                    AND UPPER(i.name_first) LIKE '{first_name}%'
                ORDER BY i.name_last, i.name_first
                LIMIT {limit}
                """
            else:
                # Single search term - search both first and last names
                search_term = query_parts[0]
                sql_query = f"""
                SELECT DISTINCT
                    v.master_id,
                    i.name_last,
                    i.name_first,
                    i.name_middle,
                    a.standardized_address as addr_residential_line1,
                    a.city as addr_residential_city,
                    a.state as addr_residential_state,
                    a.zip_code as addr_residential_zip,
                    v.demo_age,
                    v.demo_party
                FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters` v
                JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.individuals` i
                    ON v.master_id = i.master_id
                LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.addresses` a
                    ON v.address_id = a.address_id
                WHERE UPPER(i.name_last) LIKE '{search_term}%'
                    OR UPPER(i.name_first) LIKE '{search_term}%'
                ORDER BY i.name_last, i.name_first
                LIMIT {limit}
                """
            
            # Execute query
            results = await self.bq_service.execute_query(sql_query)
            
            # Format results for typeahead
            formatted_results = []
            for row in results.get("rows", []):
                address = f"{row.get('addr_residential_line1', '')}, {row.get('addr_residential_city', '')}, {row.get('addr_residential_state', '')} {row.get('addr_residential_zip', '')}"
                formatted_results.append({
                    "master_id": row.get("master_id"),
                    "name": f"{row.get('name_last', '')}, {row.get('name_first', '')} {row.get('name_middle', '')}".strip(),
                    "address": address.strip(),
                    "age": row.get("demo_age"),
                    "party": row.get("demo_party")
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching voters: {str(e)}")
            raise
    
    async def get_voter_profile(
        self, 
        master_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive voter profile including all available information.
        """
        try:
            # Get basic voter information with names and addresses
            voter_query = f"""
            SELECT 
                v.*,
                i.name_first,
                i.name_middle,
                i.name_last,
                i.name_suffix,
                a.standardized_address as addr_residential_line1,
                '' as addr_residential_line2,
                a.city as addr_residential_city,
                a.state as addr_residential_state,
                a.zip_code as addr_residential_zip
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters` v
            LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.individuals` i
                ON v.master_id = i.master_id
            LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.addresses` a
                ON v.address_id = a.address_id
            WHERE v.master_id = '{master_id}'
            LIMIT 1
            """
            
            voter_result = await self.bq_service.execute_query(voter_query)
            
            if not voter_result.get("rows"):
                return None
            
            voter_data = voter_result["rows"][0]
            
            # Get address history if available
            address_history_query = f"""
            SELECT DISTINCT
                a.standardized_address as addr_residential_line1,
                a.city as addr_residential_city,
                a.state as addr_residential_state,
                a.zip_code as addr_residential_zip,
                MIN(v.created_at) as first_seen,
                MAX(v.updated_at) as last_seen
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters` v
            LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.addresses` a
                ON v.address_id = a.address_id
            WHERE v.master_id = '{master_id}'
            GROUP BY 
                a.standardized_address,
                a.city,
                a.state,
                a.zip_code
            ORDER BY last_seen DESC
            """
            
            address_history = await self.bq_service.execute_query(address_history_query)
            
            # Check for PDL enrichment data
            pdl_query = f"""
            SELECT *
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.pdl_enrichment`
            WHERE master_id = '{master_id}'
            LIMIT 1
            """
            
            try:
                pdl_result = await self.bq_service.execute_query(pdl_query)
                pdl_data = pdl_result.get("rows", [{}])[0] if pdl_result.get("rows") else None
            except Exception as e:
                logger.warning(f"PDL enrichment table may not exist: {e}")
                pdl_data = None
            
            # Compile comprehensive profile
            profile = {
                "basic_info": {
                    "master_id": voter_data.get("master_id"),
                    "name": {
                        "first": voter_data.get("name_first"),
                        "middle": voter_data.get("name_middle"),
                        "last": voter_data.get("name_last"),
                        "suffix": voter_data.get("name_suffix")
                    },
                    "age": voter_data.get("demo_age"),
                    "race": voter_data.get("demo_race"),
                    "party": voter_data.get("demo_party"),
                    "registration_date": voter_data.get("registration_date"),
                    "voter_status": voter_data.get("voter_status"),
                    "email": voter_data.get("email")
                },
                "current_address": {
                    "line1": voter_data.get("addr_residential_line1"),
                    "line2": voter_data.get("addr_residential_line2"),
                    "city": voter_data.get("addr_residential_city"),
                    "state": voter_data.get("addr_residential_state"),
                    "zip": voter_data.get("addr_residential_zip"),
                    "county": voter_data.get("county_name"),
                    "municipality": voter_data.get("municipality_name"),
                    "ward": voter_data.get("ward_name"),
                    "district": voter_data.get("district_name"),
                    "congressional": voter_data.get("congressional_name"),
                    "legislative": voter_data.get("legislative_name")
                },
                "address_history": address_history.get("rows", []),
                "pdl_enrichment": pdl_data,
                "voter_id": voter_data.get("id"),
                "address_id": voter_data.get("address_id")
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting voter profile: {str(e)}")
            raise
    
    async def enrich_voter(
        self, 
        master_id: str, 
        force: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger PDL enrichment for a voter.
        """
        try:
            # Check if enrichment already exists and force is False
            if not force:
                pdl_query = f"""
                SELECT *
                FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.pdl_enrichment`
                WHERE master_id = '{master_id}'
                LIMIT 1
                """
                
                try:
                    pdl_result = await self.bq_service.execute_query(pdl_query)
                    if pdl_result.get("rows"):
                        return {
                            "status": "existing",
                            "data": pdl_result["rows"][0],
                            "message": "PDL enrichment data already exists"
                        }
                except Exception:
                    pass  # Table might not exist, continue with enrichment
            
            # TODO: Implement actual PDL enrichment call
            # For now, return a placeholder response
            return {
                "status": "pending",
                "message": "PDL enrichment functionality to be implemented",
                "master_id": master_id
            }
            
        except Exception as e:
            logger.error(f"Error enriching voter: {str(e)}")
            raise
    
    async def get_voter_events(
        self,
        master_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get CRM events for a voter from Firestore.
        Includes both direct CRM events and email campaign events.
        """
        try:
            events = []
            
            # First, get the voter's email address for email campaign events
            voter_email = None
            try:
                email_query = f"""
                SELECT email
                FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters`
                WHERE master_id = '{master_id}'
                LIMIT 1
                """
                email_result = await self.bq_service.execute_query(email_query)
                if email_result.get("rows"):
                    voter_email = email_result["rows"][0].get("email")
            except Exception as e:
                logger.warning(f"Could not fetch voter email: {e}")
            
            events_ref = self.firestore_client.collection(self.events_collection)
            
            # Query 1: Get events with voter_master_id (direct CRM events)
            try:
                query1 = events_ref.where("voter_master_id", "==", master_id)
                if event_type:
                    query1 = query1.where("event_type", "==", event_type)
                query1 = query1.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
                
                for doc in query1.stream():
                    event_data = doc.to_dict()
                    event_data["event_id"] = doc.id
                    events.append(event_data)
            except Exception as e:
                logger.debug(f"No direct CRM events found: {e}")
            
            # Query 2: Get email campaign events if we have an email
            if voter_email:
                try:
                    # Email campaign events have structure: email_data.email_address
                    all_events = events_ref.limit(500).stream()  # Get more events to filter
                    
                    for doc in all_events:
                        event_data = doc.to_dict()
                        
                        # Check if this is an email campaign event for this voter
                        email_data = event_data.get("email_data", {})
                        if email_data.get("email_address") == voter_email:
                            # Format the event for display
                            formatted_event = {
                                "event_id": doc.id,
                                "event_type": event_data.get("event_type", "email_campaign"),
                                "created_at": event_data.get("timestamp", event_data.get("created_at")),
                                "notes": f"Campaign: {email_data.get('campaign_name', 'Unknown')}\nStatus: {email_data.get('status', 'Unknown')}",
                                "voter_master_id": master_id,
                                "metadata": {
                                    "campaign_id": email_data.get("campaign_id"),
                                    "campaign_name": email_data.get("campaign_name"),
                                    "email_status": email_data.get("status"),
                                    "email_address": voter_email
                                }
                            }
                            
                            # Apply event_type filter if specified
                            if not event_type or formatted_event["event_type"] == event_type:
                                events.append(formatted_event)
                                
                except Exception as e:
                    logger.debug(f"No email campaign events found: {e}")
            
            # Sort all events by created_at descending
            events.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
            
            # Apply limit
            events = events[:limit]
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting voter events: {str(e)}")
            raise
    
    async def create_event(
        self,
        voter_master_id: str,
        event_type: str,
        notes: str,
        metadata: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new CRM event in Firestore.
        """
        try:
            event_id = str(uuid.uuid4())
            event_data = {
                "event_id": event_id,
                "voter_master_id": voter_master_id,
                "event_type": event_type,
                "notes": notes,
                "metadata": metadata or {},
                "created_by": user_id or "system",
                "created_at": datetime.utcnow()
            }
            
            # Add to Firestore
            self.firestore_client.collection(self.events_collection).document(event_id).set(event_data)
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            raise
    
    async def get_voting_history(
        self,
        master_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get voting history for a voter.
        """
        try:
            # Query for voting history fields
            voting_query = f"""
            SELECT 
                -- Primary elections (Democratic)
                vote_primary_dem_2024,
                vote_primary_dem_2023,
                vote_primary_dem_2022,
                vote_primary_dem_2021,
                vote_primary_dem_2020,
                vote_primary_dem_2019,
                vote_primary_dem_2018,
                -- Primary elections (Republican)
                vote_primary_rep_2024,
                vote_primary_rep_2023,
                vote_primary_rep_2022,
                vote_primary_rep_2021,
                vote_primary_rep_2020,
                vote_primary_rep_2019,
                vote_primary_rep_2018,
                -- General elections
                participation_general_2024,
                participation_general_2023,
                participation_general_2022,
                participation_general_2021,
                participation_general_2020,
                participation_general_2019,
                participation_general_2018
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters`
            WHERE master_id = '{master_id}'
            LIMIT 1
            """
            
            result = await self.bq_service.execute_query(voting_query)
            
            if not result.get("rows"):
                return {"primaries": [], "generals": []}
            
            voting_data = result["rows"][0]
            
            # Parse voting history
            primaries = []
            generals = []
            
            for key, value in voting_data.items():
                if value:  # Only include if they voted
                    if "primary_dem" in key:
                        year = key.split("_")[-1]
                        primaries.append({"year": year, "party": "DEM", "voted": True})
                    elif "primary_rep" in key:
                        year = key.split("_")[-1]
                        primaries.append({"year": year, "party": "REP", "voted": True})
                    elif "general" in key:
                        year = key.split("_")[-1]
                        generals.append({"year": year, "voted": True})
            
            # Sort by year descending
            primaries.sort(key=lambda x: x["year"], reverse=True)
            generals.sort(key=lambda x: x["year"], reverse=True)
            
            return {
                "primaries": primaries,
                "generals": generals
            }
            
        except Exception as e:
            logger.error(f"Error getting voting history: {str(e)}")
            raise
    
    async def get_donation_history(
        self,
        master_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get donation history for a voter.
        """
        try:
            # Query donations table
            donations_query = f"""
            SELECT 
                d.committee_name as recipient,
                d.contribution_amount as amount,
                d.donation_date as date,
                d.election_type,
                d.election_year,
                d.employer as contributor_employer,
                d.occupation as contributor_occupation,
                d.match_confidence,
                d.match_method,
                d.original_full_name,
                d.original_address
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.donations` d
            WHERE d.master_id = '{master_id}'
            ORDER BY d.donation_date DESC
            LIMIT 100
            """
            
            result = await self.bq_service.execute_query(donations_query)
            
            donations = result.get("rows", [])
            
            # Calculate summary statistics
            total_amount = sum(float(d.get("amount", 0)) for d in donations)
            num_donations = len(donations)
            
            # Group by recipient
            by_recipient = {}
            for donation in donations:
                recipient = donation.get("recipient", "Unknown")
                if recipient not in by_recipient:
                    by_recipient[recipient] = {
                        "count": 0,
                        "total": 0,
                        "donations": []
                    }
                by_recipient[recipient]["count"] += 1
                by_recipient[recipient]["total"] += float(donation.get("amount", 0))
                by_recipient[recipient]["donations"].append(donation)
            
            return {
                "summary": {
                    "total_amount": total_amount,
                    "num_donations": num_donations,
                    "num_recipients": len(by_recipient)
                },
                "donations": donations,
                "by_recipient": by_recipient
            }
            
        except Exception as e:
            logger.error(f"Error getting donation history: {str(e)}")
            raise