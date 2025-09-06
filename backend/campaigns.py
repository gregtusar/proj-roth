"""Campaign management module for email campaigns."""

import uuid
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import sendgrid
from sendgrid.helpers.mail import Mail, To, CustomArg, Personalization
from firebase_admin import firestore
from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import os

logger = logging.getLogger(__name__)

class CampaignManager:
    """Manages email campaigns with SendGrid integration."""
    
    def __init__(self, firestore_client, bigquery_client):
        self.db = firestore_client
        self.bq = bigquery_client
        self.sg = self._init_sendgrid()
        self.docs_service = self._init_docs_service()
        
    def _init_sendgrid(self):
        """Initialize SendGrid client with API key from Secret Manager."""
        try:
            logger.info("[SENDGRID] Initializing SendGrid client...")
            client = secretmanager.SecretManagerServiceClient()
            project_id = "proj-roth"
            secret_name = f"projects/{project_id}/secrets/sendgrid-api-key/versions/latest"
            logger.info(f"[SENDGRID] Fetching API key from Secret Manager: {secret_name}")
            
            response = client.access_secret_version(request={"name": secret_name})
            api_key = response.payload.data.decode("UTF-8")
            
            # Log API key details (first/last few chars for verification)
            masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "KEY_TOO_SHORT"
            logger.info(f"[SENDGRID] API key retrieved successfully: {masked_key}")
            
            sg_client = sendgrid.SendGridAPIClient(api_key=api_key)
            logger.info("[SENDGRID] SendGrid client initialized successfully")
            return sg_client
        except Exception as e:
            logger.error(f"[SENDGRID] Failed to initialize SendGrid: {e}")
            import traceback
            logger.error(f"[SENDGRID] Traceback: {traceback.format_exc()}")
            return None
    
    def _init_docs_service(self):
        """Initialize Google Docs service."""
        try:
            # Try to use service account credentials
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=['https://www.googleapis.com/auth/documents.readonly']
                )
            else:
                # Use default credentials
                from google.auth import default
                credentials, _ = default(scopes=['https://www.googleapis.com/auth/documents.readonly'])
            
            return build('docs', 'v1', credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs service: {e}")
            return None
    
    def fetch_google_doc_content(self, google_doc_url: str) -> str:
        """Fetch content from a Google Doc URL."""
        if not self.docs_service:
            logger.error("Google Docs service not initialized")
            return """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Error: Google Docs Service Not Available</h2>
                <p>The email service could not connect to Google Docs. Please contact support.</p>
            </div>
            """
        
        try:
            # Extract document ID from URL
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', google_doc_url)
            if not doc_id_match:
                raise ValueError(f"Invalid Google Docs URL: {google_doc_url}")
            
            doc_id = doc_id_match.group(1)
            logger.info(f"[GOOGLE_DOC] Fetching document ID: {doc_id}")
            
            # Fetch the document
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            
            # Extract and convert content to HTML
            html_content = self._convert_doc_to_html(document)
            logger.info(f"[GOOGLE_DOC] Successfully fetched document content")
            
            return html_content
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[GOOGLE_DOC] Failed to fetch content: {error_msg}")
            
            # Check for permission errors
            if "403" in error_msg or "permission" in error_msg.lower():
                return f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #f44336; background: #ffebee; border-radius: 8px;">
                    <h2 style="color: #d32f2f;">⚠️ Google Doc Access Error</h2>
                    <p><strong>The email service cannot access the Google Doc.</strong></p>
                    <p>To fix this, please:</p>
                    <ol>
                        <li>Open your Google Doc: <a href="{google_doc_url}" target="_blank">Click here</a></li>
                        <li>Click the "Share" button (top right)</li>
                        <li>Click "Change to anyone with the link"</li>
                        <li>Set permission to "Viewer"</li>
                        <li>Click "Done"</li>
                    </ol>
                    <p style="color: #666; font-size: 12px;">Alternatively, share with: nj-voter-chat-app@proj-roth.iam.gserviceaccount.com</p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ccc;">
                    <p style="font-size: 11px; color: #999;">Error details: {error_msg}</p>
                </div>
                """
            else:
                return f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #ff9800; background: #fff3e0; border-radius: 8px;">
                    <h2 style="color: #e65100;">📄 Document Error</h2>
                    <p>Unable to fetch the Google Doc content.</p>
                    <p>Error: {error_msg}</p>
                    <p>Please check the document URL and try again.</p>
                </div>
                """
    
    def _convert_doc_to_html(self, document: Dict) -> str:
        """Convert Google Docs content to HTML for email."""
        html_parts = []
        
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph_html = self._process_paragraph(element['paragraph'])
                if paragraph_html:
                    html_parts.append(paragraph_html)
        
        # Wrap in basic HTML structure
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            {''.join(html_parts)}
            <hr style="margin-top: 40px; border: none; border-top: 1px solid #ccc;">
            <p style="font-size: 12px; color: #666; text-align: center;">
                <a href="{{{{unsubscribe_url}}}}">Unsubscribe</a> from future emails
            </p>
        </div>
        """
        
        return html_content
    
    def _process_paragraph(self, paragraph: Dict) -> str:
        """Process a paragraph element into HTML."""
        text_parts = []
        
        for element in paragraph.get('elements', []):
            if 'textRun' in element:
                text_run = element['textRun']
                content = text_run.get('content', '')
                
                # Skip empty paragraphs
                if not content.strip():
                    continue
                
                # Apply text styling
                style = text_run.get('textStyle', {})
                styled_text = content
                
                if style.get('bold'):
                    styled_text = f"<strong>{styled_text}</strong>"
                if style.get('italic'):
                    styled_text = f"<em>{styled_text}</em>"
                if style.get('underline'):
                    styled_text = f"<u>{styled_text}</u>"
                
                text_parts.append(styled_text)
        
        if text_parts:
            full_text = ''.join(text_parts)
            
            # Determine paragraph style based on content
            style = paragraph.get('paragraphStyle', {})
            named_style = style.get('namedStyleType', 'NORMAL_TEXT')
            
            if named_style == 'HEADING_1':
                return f"<h1>{full_text}</h1>"
            elif named_style == 'HEADING_2':
                return f"<h2>{full_text}</h2>"
            elif named_style == 'HEADING_3':
                return f"<h3>{full_text}</h3>"
            else:
                return f"<p>{full_text}</p>"
        
        return ""
    
    def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new campaign in Firestore."""
        campaign_id = str(uuid.uuid4())
        campaign = {
            'campaign_id': campaign_id,
            'name': campaign_data['name'],
            'list_id': campaign_data['list_id'],
            'subject_line': campaign_data['subject_line'],
            'google_doc_url': campaign_data['google_doc_url'],
            'created_at': firestore.SERVER_TIMESTAMP,
            'created_by': campaign_data.get('created_by', 'system'),
            'sent_at': None,
            'status': 'draft',
            'sendgrid_batch_id': None,
            'stats': {
                'total_recipients': 0,
                'sent': 0,
                'delivered': 0,
                'opened': 0,
                'clicked': 0,
                'bounced': 0,
                'last_updated': firestore.SERVER_TIMESTAMP
            }
        }
        
        self.db.collection('campaigns').document(campaign_id).set(campaign)
        return campaign_id
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Get campaign details."""
        doc = self.db.collection('campaigns').document(campaign_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def list_campaigns(self, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
        """List campaigns with optional filtering."""
        query = self.db.collection('campaigns')
        
        if status:
            query = query.where('status', '==', status)
        
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        query = query.limit(limit).offset(offset)
        
        campaigns = []
        for doc in query.stream():
            campaign = doc.to_dict()
            campaigns.append(campaign)
        
        return campaigns
    
    def update_campaign(self, campaign_id: str, updates: Dict) -> bool:
        """Update campaign details."""
        try:
            self.db.collection('campaigns').document(campaign_id).update(updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update campaign {campaign_id}: {e}")
            return False
    
    def get_list_recipients(self, list_id: str) -> List[Dict]:
        """Get recipients from a saved list with their emails from BigQuery."""
        logger.info(f"[RECIPIENTS] Getting recipients for list {list_id}")
        
        # Get the saved list - check both collections (lists and voter_lists)
        list_doc = self.db.collection('lists').document(list_id).get()
        if not list_doc.exists:
            # Try the voter_lists collection
            list_doc = self.db.collection('voter_lists').document(list_id).get()
            if not list_doc.exists:
                logger.error(f"[RECIPIENTS] List {list_id} not found in either collection")
                return []
        
        list_data = list_doc.to_dict()
        logger.info(f"[RECIPIENTS] List data keys: {list_data.keys()}")
        
        # Lists store a SQL query, not voter_ids
        list_query = list_data.get('query', '')
        
        if not list_query:
            logger.error(f"[RECIPIENTS] No query found in list {list_id}")
            return []
        
        logger.info(f"[RECIPIENTS] Executing list query to get voter IDs...")
        logger.info(f"[RECIPIENTS] Query preview: {list_query[:200]}...")
        
        try:
            # STEP 1: Wrap the list query to ensure we get voter IDs
            # If the query doesn't select an ID field, we need to get it from the table
            
            # Check if the query already has an ID field
            query_lower = list_query.lower()
            has_id_field = any(field in query_lower for field in ['id', 'master_id', 'voter_id', 'voter_record_id'])
            
            if not has_id_field:
                # Wrap the query to extract IDs from whatever table it's querying
                # Try to detect the table name from the FROM clause
                if 'voter_geo_view' in query_lower:
                    # For voter_geo_view, we need master_id
                    wrapped_query = f"""
                    WITH list_results AS ({list_query})
                    SELECT DISTINCT v.master_id as id
                    FROM list_results lr
                    JOIN `proj-roth.voter_data.voter_geo_view` v
                    ON v.standardized_name = lr.standardized_name
                    """
                elif 'voters' in query_lower:
                    # For voters table, use id
                    wrapped_query = f"""
                    SELECT DISTINCT id FROM ({list_query}) AS subquery
                    """
                else:
                    # Generic approach - try to join back to voters
                    logger.warning("[RECIPIENTS] Query doesn't select ID - attempting to extract from results")
                    wrapped_query = list_query
            else:
                wrapped_query = list_query
            
            logger.info(f"[RECIPIENTS] Executing query to get voter IDs...")
            query_job = self.bq.query(wrapped_query)
            list_results = query_job.result()
            
            # Extract voter IDs from the results
            voter_ids = []
            for row in list_results:
                # Check for various ID field names in order of preference
                voter_id = None
                if hasattr(row, 'id'):
                    voter_id = row.id
                elif hasattr(row, 'master_id'):
                    voter_id = row.master_id
                elif hasattr(row, 'voter_id'):
                    voter_id = row.voter_id
                elif hasattr(row, 'voter_record_id'):
                    voter_id = row.voter_record_id
                
                if voter_id:
                    voter_ids.append(str(voter_id))
            
            logger.info(f"[RECIPIENTS] Found {len(voter_ids)} voter IDs from list query")
            
            if not voter_ids:
                logger.error(f"[RECIPIENTS] No voter IDs found - the list query must include an ID field (id, master_id, voter_id, etc.)")
                logger.error(f"[RECIPIENTS] Original query: {list_query[:200]}")
                return []
            
            # STEP 2: Now independently fetch email addresses for these voter IDs
            # This is a separate query that the campaign system controls
            # Limit to 1000 IDs per query for safety (can batch if needed)
            if len(voter_ids) > 1000:
                logger.warning(f"[RECIPIENTS] List has {len(voter_ids)} voters, limiting to first 1000 for email campaign")
                voter_ids = voter_ids[:1000]
            
            # Convert voter_ids list to SQL-safe format
            voter_ids_str = "','".join(voter_ids)
            
            # Campaign-specific query to get the fields WE need for emails
            email_query = f"""
            SELECT DISTINCT
                id as master_id,
                name_first as first_name,
                name_last as last_name,
                email,
                addr_residential_city as city
            FROM `proj-roth.voter_data.voters`
            WHERE id IN ('{voter_ids_str}')
            AND email IS NOT NULL
            AND email != ''
            AND LENGTH(email) > 3
            AND email LIKE '%@%'
            """
            
            logger.info(f"[RECIPIENTS] Fetching email addresses for {len(voter_ids)} voters...")
            
            query_job = self.bq.query(email_query)
            results = query_job.result()
            
            recipients = []
            for row in results:
                recipients.append({
                    'master_id': row.master_id,
                    'email': row.email,
                    'first_name': row.first_name or '',
                    'last_name': row.last_name or '',
                    'city': row.city or ''
                })
            
            logger.info(f"[RECIPIENTS] Found {len(recipients)} recipients with valid emails out of {len(voter_ids)} voters")
            
            if len(recipients) == 0 and len(voter_ids) > 0:
                logger.warning(f"[RECIPIENTS] No email addresses found for {len(voter_ids)} voters in the list")
            
            return recipients
            
        except Exception as e:
            logger.error(f"[RECIPIENTS] Failed to fetch recipients: {e}")
            import traceback
            logger.error(f"[RECIPIENTS] Traceback: {traceback.format_exc()}")
            return []
    
    def send_campaign(self, campaign_id: str, test_email: Optional[str] = None) -> Dict:
        """Send a campaign to all recipients or test email."""
        logger.info(f"[CAMPAIGN] Starting send_campaign for campaign_id: {campaign_id}, test_email: {test_email}")
        
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            logger.error(f"[CAMPAIGN] Campaign {campaign_id} not found")
            return {'success': False, 'error': 'Campaign not found'}
        
        logger.info(f"[CAMPAIGN] Campaign found: {campaign['name']}")
        
        # Get email content from Google Docs
        logger.info(f"[CAMPAIGN] Fetching content from Google Doc: {campaign['google_doc_url']}")
        email_content = self.fetch_google_doc_content(campaign['google_doc_url'])
        logger.info(f"[CAMPAIGN] Email content fetched, length: {len(email_content)} characters")
        
        if test_email:
            # Send test email
            logger.info(f"[CAMPAIGN] Preparing test email to: {test_email}")
            recipients = [{
                'master_id': 'TEST',
                'email': test_email,
                'first_name': 'Test',
                'last_name': 'User',
                'city': 'Test City'
            }]
        else:
            # Get all recipients
            logger.info(f"[CAMPAIGN] Fetching recipients from list: {campaign['list_id']}")
            recipients = self.get_list_recipients(campaign['list_id'])
            logger.info(f"[CAMPAIGN] Found {len(recipients)} recipients with emails")
        
        if not recipients:
            logger.error("[CAMPAIGN] No recipients found")
            return {'success': False, 'error': 'No recipients found'}
        
        # Update campaign status
        self.update_campaign(campaign_id, {
            'status': 'sending',
            'stats.total_recipients': len(recipients)
        })
        
        # Send emails in batches
        batch_id = str(uuid.uuid4())
        batch_size = 1000
        sent_count = 0
        
        logger.info(f"[CAMPAIGN] Starting email send - Total recipients: {len(recipients)}")
        logger.info(f"[CAMPAIGN] Batch ID: {batch_id}, Batch size: {batch_size}")
        
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            logger.info(f"[CAMPAIGN] Sending batch {i//batch_size + 1} ({len(batch)} recipients)")
            
            success = self._send_batch(
                batch, 
                campaign['subject_line'],
                email_content,
                campaign_id,
                batch_id
            )
            
            if success:
                sent_count += len(batch)
                logger.info(f"[CAMPAIGN] Batch sent successfully. Total sent so far: {sent_count}")
            else:
                logger.error(f"[CAMPAIGN] Batch failed. Sent count remains: {sent_count}")
                
                # Create events for sent emails
                for recipient in batch:
                    self._create_event({
                        'master_id': recipient['master_id'],
                        'event_type': 'email_sent',
                        'email_data': {
                            'campaign_id': campaign_id,
                            'email_address': recipient['email'],
                            'subject_line': campaign['subject_line'],
                            'sendgrid_batch_id': batch_id
                        }
                    })
        
        # Update campaign status
        final_status = 'sent' if sent_count == len(recipients) else 'partial'
        self.update_campaign(campaign_id, {
            'status': final_status,
            'sent_at': firestore.SERVER_TIMESTAMP,
            'sendgrid_batch_id': batch_id,
            'stats.sent': sent_count
        })
        
        return {
            'success': True,
            'sent_count': sent_count,
            'total_recipients': len(recipients)
        }
    
    def _send_batch(self, recipients: List[Dict], subject: str, content: str, 
                    campaign_id: str, batch_id: str) -> bool:
        """Send a batch of emails via SendGrid."""
        logger.info(f"[SENDGRID] Starting _send_batch for {len(recipients)} recipients")
        logger.info(f"[SENDGRID] Campaign ID: {campaign_id}, Batch ID: {batch_id}")
        logger.info(f"[SENDGRID] Subject: {subject}")
        
        if not self.sg:
            logger.error("[SENDGRID] SendGrid client not initialized")
            return False
        
        logger.info("[SENDGRID] SendGrid client is available")
        
        try:
            logger.info("[SENDGRID] Creating Mail object...")
            message = Mail()
            message.from_email = "gregtusar@gwanalytica.ai"  # Update with your verified sender
            message.subject = subject
            message.html_content = content
            logger.info(f"[SENDGRID] Mail object created with from_email: gregtusar@gwanalytica.ai")
            
            # Add personalizations for each recipient
            logger.info(f"[SENDGRID] Adding personalizations for {len(recipients)} recipients...")
            for i, recipient in enumerate(recipients):
                logger.info(f"[SENDGRID] Processing recipient {i+1}/{len(recipients)}: {recipient['email']}")
                personalization = Personalization()
                personalization.add_to(To(
                    email=recipient['email'],
                    name=f"{recipient['first_name']} {recipient['last_name']}"
                ))
                
                # Add substitution tags for personalization
                personalization.add_substitution("{{first_name}}", recipient['first_name'])
                personalization.add_substitution("{{last_name}}", recipient['last_name'])
                personalization.add_substitution("{{city}}", recipient['city'])
                
                # Add custom args for tracking
                personalization.add_custom_arg(CustomArg("campaign_id", campaign_id))
                personalization.add_custom_arg(CustomArg("master_id", recipient['master_id']))
                personalization.add_custom_arg(CustomArg("batch_id", batch_id))
                
                message.add_personalization(personalization)
            
            logger.info("[SENDGRID] All personalizations added")
            
            # Send the batch
            logger.info("[SENDGRID] Sending email batch to SendGrid API...")
            response = self.sg.send(message)
            
            logger.info(f"[SENDGRID] Response received - Status Code: {response.status_code}")
            logger.info(f"[SENDGRID] Response Headers: {response.headers}")
            logger.info(f"[SENDGRID] Response Body: {response.body}")
            
            if response.status_code in [200, 202]:
                logger.info(f"[SENDGRID] SUCCESS - Batch sent successfully: {len(recipients)} recipients")
                logger.info(f"[SENDGRID] Message ID: {response.headers.get('X-Message-Id', 'N/A')}")
                return True
            else:
                logger.error(f"[SENDGRID] FAILED - SendGrid error: {response.status_code}")
                logger.error(f"[SENDGRID] Error body: {response.body}")
                logger.error(f"[SENDGRID] Error headers: {response.headers}")
                return False
                
        except Exception as e:
            logger.error(f"[SENDGRID] EXCEPTION in _send_batch: {e}")
            import traceback
            logger.error(f"[SENDGRID] Traceback: {traceback.format_exc()}")
            return False
    
    def _create_event(self, event_data: Dict):
        """Create an event record in Firestore."""
        event_id = str(uuid.uuid4())
        event = {
            'event_id': event_id,
            'timestamp': firestore.SERVER_TIMESTAMP,
            **event_data
        }
        self.db.collection('events').document(event_id).set(event)
    
    def handle_sendgrid_webhook(self, events: List[Dict]):
        """Process SendGrid webhook events."""
        event_type_map = {
            'delivered': 'email_delivered',
            'open': 'email_opened',
            'click': 'email_clicked',
            'bounce': 'email_bounced',
            'dropped': 'email_dropped',
            'unsubscribe': 'email_unsubscribed',
            'spamreport': 'email_spam_reported'
        }
        
        for sg_event in events:
            # Extract custom args
            campaign_id = sg_event.get('campaign_id')
            master_id = sg_event.get('master_id')
            
            if not campaign_id or not master_id:
                logger.warning(f"Missing tracking data in webhook event: {sg_event}")
                continue
            
            # Create our event record
            event_type = event_type_map.get(sg_event['event'], sg_event['event'])
            
            event_data = {
                'master_id': master_id,
                'event_type': event_type,
                'email_data': {
                    'campaign_id': campaign_id,
                    'email_address': sg_event.get('email'),
                    'sendgrid_event_id': sg_event.get('sg_event_id'),
                    'sendgrid_message_id': sg_event.get('sg_message_id')
                }
            }
            
            # Add interaction data for opens/clicks
            if event_type in ['email_opened', 'email_clicked']:
                event_data['interaction_data'] = {
                    'ip_address': sg_event.get('ip'),
                    'user_agent': sg_event.get('useragent'),
                    'clicked_url': sg_event.get('url')
                }
            
            # Add bounce reason if present
            if event_type == 'email_bounced':
                event_data['email_data']['bounce_reason'] = sg_event.get('reason')
            
            self._create_event(event_data)
            
            # Update campaign stats
            self._update_campaign_stats(campaign_id, sg_event['event'])
    
    def _update_campaign_stats(self, campaign_id: str, event_type: str):
        """Update campaign statistics based on events."""
        stat_field_map = {
            'delivered': 'stats.delivered',
            'open': 'stats.opened',
            'click': 'stats.clicked',
            'bounce': 'stats.bounced',
            'dropped': 'stats.bounced',
            'unsubscribe': 'stats.unsubscribed'
        }
        
        field = stat_field_map.get(event_type)
        if field:
            try:
                self.db.collection('campaigns').document(campaign_id).update({
                    field: firestore.Increment(1),
                    'stats.last_updated': firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                logger.error(f"Failed to update campaign stats: {e}")
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get detailed statistics for a campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        # Get event counts by type
        events_ref = self.db.collection('events')
        event_counts = {}
        
        event_types = ['email_sent', 'email_delivered', 'email_opened', 
                      'email_clicked', 'email_bounced', 'email_unsubscribed']
        
        for event_type in event_types:
            query = events_ref.where('event_type', '==', event_type)\
                             .where('email_data.campaign_id', '==', campaign_id)
            count = len(list(query.stream()))
            event_counts[event_type] = count
        
        # Calculate rates
        total = campaign['stats']['total_recipients']
        if total > 0:
            stats = {
                'total_recipients': total,
                'sent': event_counts.get('email_sent', 0),
                'delivered': event_counts.get('email_delivered', 0),
                'opened': event_counts.get('email_opened', 0),
                'clicked': event_counts.get('email_clicked', 0),
                'bounced': event_counts.get('email_bounced', 0),
                'unsubscribed': event_counts.get('email_unsubscribed', 0),
                'delivery_rate': (event_counts.get('email_delivered', 0) / total) * 100,
                'open_rate': (event_counts.get('email_opened', 0) / total) * 100,
                'click_rate': (event_counts.get('email_clicked', 0) / total) * 100,
                'bounce_rate': (event_counts.get('email_bounced', 0) / total) * 100
            }
        else:
            stats = campaign['stats']
        
        return stats
