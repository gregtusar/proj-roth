# Email Campaign Implementation Plan

## Overview
This document outlines the implementation plan for adding email campaign capabilities to the NJ Voter Chat platform, leveraging existing list functionality and Google Docs integration.

## Core Concepts

### Events System (Universal Tracking)
All interactions with voters (master_id) will be tracked through a unified events system that can handle multiple interaction types:
- Email events (sent, opened, clicked, bounced)
- Future: SMS, phone calls, in-person meetings, etc.

### Integration with Existing Systems
- **Lists**: Use existing saved voter lists (already implemented)
- **Google Docs**: Reuse existing Google Docs integration for email content
- **Master ID**: All events linked to voter master_id from BigQuery data

## Data Architecture

### 1. Campaigns Collection
```javascript
// firestore: campaigns/{campaign_id}
{
  campaign_id: "auto-generated",
  name: "November GOTV Campaign",
  list_id: "existing-list-id",  // References existing saved list
  subject_line: "Your vote matters this November",
  google_doc_url: "https://docs.google.com/document/d/xxx",
  
  // Metadata
  created_at: timestamp,
  created_by: "user_id",
  sent_at: timestamp | null,
  status: "draft" | "sending" | "sent" | "failed",
  
  // SendGrid tracking
  sendgrid_batch_id: "xxx" | null,
  
  // Denormalized stats for quick display
  stats: {
    total_recipients: 0,
    sent: 0,
    delivered: 0,
    opened: 0,
    clicked: 0,
    bounced: 0,
    last_updated: timestamp
  }
}
```

### 2. Events Collection (Universal)
```javascript
// firestore: events/{event_id}
{
  event_id: "auto-generated-uuid",
  master_id: "V123456",  // Links to voter
  timestamp: timestamp,
  event_type: "email_sent" | "email_opened" | "email_clicked" | "email_bounced" | 
              "sms_sent" | "sms_replied" | "call_made" | "meeting_held" | etc.,
  
  // Event-specific data (varies by type)
  // For email events:
  email_data: {
    campaign_id: "campaign_xyz",
    email_address: "john.doe@email.com",
    subject_line: "...",
    sendgrid_message_id: "xxx",
    sendgrid_event_id: "xxx"  // For deduplication
  },
  
  // For email open/click events:
  interaction_data: {
    ip_address: "xxx.xxx.xxx.xxx",
    user_agent: "Mozilla/5.0...",
    clicked_url: "https://..." | null
  },
  
  // For future SMS events:
  sms_data: {
    phone_number: "xxx-xxx-xxxx",
    message: "...",
    direction: "outbound" | "inbound",
    twilio_message_sid: "xxx"
  },
  
  // For future call events:
  call_data: {
    phone_number: "xxx-xxx-xxxx",
    duration_seconds: 120,
    outcome: "answered" | "voicemail" | "no_answer",
    notes: "..."
  }
}
```

### 3. Firestore Indexes Required
```
// events collection indexes
master_id, timestamp DESC
event_type, timestamp DESC
email_data.campaign_id, timestamp DESC

// campaigns collection indexes
status, created_at DESC
created_by, created_at DESC
```

## Backend API Implementation

### New Endpoints in `backend/main.py`

#### Campaign Management
```python
# Create campaign
POST /api/campaigns
Body: {
  name: string,
  list_id: string,
  subject_line: string,
  google_doc_url: string
}

# List campaigns
GET /api/campaigns
Query params: ?status=sent&limit=20&offset=0

# Get campaign details with stats
GET /api/campaigns/{campaign_id}

# Send campaign
POST /api/campaigns/{campaign_id}/send

# Send test email
POST /api/campaigns/{campaign_id}/test
Body: { test_email: "test@example.com" }
```

#### Campaign Analytics
```python
# Get campaign statistics
GET /api/campaigns/{campaign_id}/stats

# Get campaign events
GET /api/campaigns/{campaign_id}/events
Query params: ?event_type=email_opened&limit=100
```

#### SendGrid Webhook
```python
# Receive SendGrid events
POST /api/webhooks/sendgrid
```

### Implementation Details

#### Sending Flow
```python
@app.route('/api/campaigns/<campaign_id>/send', methods=['POST'])
async def send_campaign(campaign_id):
    # 1. Get campaign
    campaign = firestore_client.collection('campaigns').document(campaign_id).get()
    
    # 2. Get list recipients (reuse existing list functionality)
    list_data = get_saved_list(campaign['list_id'])
    recipients = list_data['voter_ids']  # Array of master_ids
    
    # 3. Get voter emails from BigQuery
    voter_emails = fetch_voter_emails(recipients)  # Query voters table
    
    # 4. Get email content (reuse existing Google Docs integration)
    email_html = fetch_google_doc_content(campaign['google_doc_url'])
    
    # 5. Send via SendGrid with batching
    batch_id = str(uuid.uuid4())
    for batch in chunk(voter_emails, 1000):
        send_batch_via_sendgrid(
            batch, 
            email_html,
            campaign['subject_line'],
            campaign_id,
            batch_id
        )
    
    # 6. Create initial events
    for voter in voter_emails:
        create_event({
            'master_id': voter['master_id'],
            'event_type': 'email_sent',
            'email_data': {
                'campaign_id': campaign_id,
                'email_address': voter['email'],
                'subject_line': campaign['subject_line']
            }
        })
    
    # 7. Update campaign status
    update_campaign_status(campaign_id, 'sent', batch_id)
    
    return {'status': 'success', 'recipients': len(voter_emails)}
```

#### SendGrid Webhook Handler
```python
@app.route('/api/webhooks/sendgrid', methods=['POST'])
async def handle_sendgrid_webhook():
    events = request.json
    
    for event in events:
        # Extract custom args we passed
        campaign_id = event.get('campaign_id')
        master_id = event.get('master_id')
        
        # Map SendGrid event to our event type
        event_type_map = {
            'delivered': 'email_delivered',
            'open': 'email_opened',
            'click': 'email_clicked',
            'bounce': 'email_bounced',
            'unsubscribe': 'email_unsubscribed'
        }
        
        # Create event record
        create_event({
            'master_id': master_id,
            'event_type': event_type_map.get(event['event']),
            'email_data': {
                'campaign_id': campaign_id,
                'sendgrid_event_id': event.get('sg_event_id'),
                'email_address': event.get('email')
            },
            'interaction_data': {
                'ip_address': event.get('ip'),
                'user_agent': event.get('useragent'),
                'clicked_url': event.get('url')
            }
        })
        
        # Update campaign stats
        increment_campaign_stat(campaign_id, event['event'])
    
    return {'received': True}
```

## Frontend Implementation

### Campaign Manager UI Components

Location: `frontend/src/components/campaigns/`

```
CampaignManager.tsx       # Main container
├── CampaignList.tsx     # List of all campaigns
├── CampaignCreate.tsx   # Create new campaign form
├── CampaignDetail.tsx   # View single campaign
└── CampaignStats.tsx    # Statistics dashboard
```

### Key UI Features

1. **Campaign List View**
   - Table with: Name, List, Status, Sent Date, Open Rate, Click Rate
   - Multi-select for comparing campaigns
   - Filter by status (draft/sent)

2. **Create Campaign Flow**
   - Step 1: Name campaign
   - Step 2: Select existing list
   - Step 3: Enter subject line
   - Step 4: Paste Google Doc URL
   - Step 5: Preview and send test
   - Step 6: Send to list

3. **Statistics Dashboard**
   - Real-time stats per campaign
   - Comparative view for multiple campaigns
   - Metrics: Sent, Delivered, Opened, Clicked, Bounced
   - Export to CSV functionality

## SendGrid Configuration

### Required Setup
1. SendGrid API key in Secret Manager: `sendgrid-api-key`
2. Verified sender domain/email
3. Webhook configuration pointing to `/api/webhooks/sendgrid`

### Custom Arguments for Tracking
```javascript
// Pass with every email
{
  "custom_args": {
    "campaign_id": "xxx",
    "master_id": "V123456"
  }
}
```

## Implementation Phases

### Phase 1: Backend Foundation (Days 1-2)
- [ ] Create Firestore collections and indexes
- [ ] Implement campaign CRUD endpoints
- [ ] Set up SendGrid SDK integration
- [ ] Create events system

### Phase 2: Email Sending (Days 3-4)
- [ ] Implement batch sending logic
- [ ] Integrate with existing lists
- [ ] Reuse Google Docs fetching
- [ ] Add email validation/cleaning

### Phase 3: Event Tracking (Days 5-6)
- [ ] Implement SendGrid webhook handler
- [ ] Create event storage logic
- [ ] Build statistics aggregation
- [ ] Test event deduplication

### Phase 4: Frontend UI (Days 7-9)
- [ ] Build Campaign Manager components
- [ ] Create campaign creation flow
- [ ] Implement statistics dashboard
- [ ] Add multi-campaign comparison

### Phase 5: Testing & Refinement (Days 10-11)
- [ ] End-to-end testing
- [ ] Load testing with large lists
- [ ] UI polish and error handling
- [ ] Documentation

## Security Considerations

1. **Authentication**: All API endpoints require authenticated user
2. **Rate Limiting**: Implement limits on campaign sending
3. **Email Validation**: Clean and validate emails before sending
4. **Unsubscribe Handling**: Automatic unsubscribe link in all emails
5. **Audit Logging**: Track all campaign actions

## Future Extensibility

The events system is designed to handle future communication channels:
- SMS campaigns (via Twilio)
- Phone banking tracking
- In-person canvassing
- Direct mail campaigns

Each will create events with appropriate type and data structure, allowing unified reporting across all voter contact methods.

## Questions to Resolve

1. Email source: Where do voter emails come from? BigQuery voters table or separate source?
2. Unsubscribe management: How to handle opt-outs across campaigns?
3. Template personalization: What merge fields needed beyond first/last name?
4. Rate limits: Expected volume per campaign? Daily sending limits?
5. Bounce handling: Auto-remove hard bounces from future campaigns?

## Next Steps

Once this plan is approved:
1. Set up SendGrid account and API key
2. Create Firestore collections
3. Begin backend implementation
4. Build frontend components in parallel