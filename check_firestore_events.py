#!/usr/bin/env python
"""
Script to examine Firestore events and campaign data
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'proj-roth'
    })

db = firestore.client()

print("=" * 80)
print("EXAMINING FIRESTORE DATA FOR CAMPAIGN 'test15'")
print("=" * 80)

# First, find the test15 campaign
print("\n1. SEARCHING FOR CAMPAIGN 'test15'...")
campaigns = db.collection('campaigns').where('name', '==', 'test15').stream()
campaign_found = False

for campaign in campaigns:
    campaign_found = True
    campaign_data = campaign.to_dict()
    campaign_id = campaign.id
    
    print(f"\n✓ Found campaign:")
    print(f"  - Campaign ID: {campaign_id}")
    print(f"  - Name: {campaign_data.get('name')}")
    print(f"  - Status: {campaign_data.get('status')}")
    stats = campaign_data.get('stats', {})
    # Convert timestamps to strings for JSON serialization
    stats_json = {}
    for k, v in stats.items():
        if hasattr(v, 'isoformat'):
            stats_json[k] = v.isoformat()
        else:
            stats_json[k] = v
    print(f"  - Stats: {json.dumps(stats_json, indent=4)}")
    print(f"  - Created: {campaign_data.get('created_at')}")
    print(f"  - Sent: {campaign_data.get('sent_at')}")
    
    # Now look for events with this campaign_id
    print(f"\n2. SEARCHING FOR EVENTS WITH campaign_id = '{campaign_id}'...")
    
    # Get ALL events first to see what's there
    events_ref = db.collection('events')
    all_events = list(events_ref.limit(100).stream())
    
    print(f"\n  Total events in collection (first 100): {len(all_events)}")
    
    # Show structure of first few events
    print("\n  Sample event structures (first 3):")
    for i, event in enumerate(all_events[:3], 1):
        event_data = event.to_dict()
        print(f"\n  Event {i}:")
        print(f"    - Document ID: {event.id}")
        print(f"    - event_type: {event_data.get('event_type')}")
        print(f"    - email_data: {json.dumps(event_data.get('email_data', {}), indent=8)}")
        if 'master_id' in event_data:
            print(f"    - master_id: {event_data.get('master_id')}")
        if 'timestamp' in event_data:
            print(f"    - timestamp: {event_data.get('timestamp')}")
    
    # Now look specifically for events matching this campaign
    print(f"\n3. FILTERING EVENTS FOR campaign_id = '{campaign_id}'...")
    
    matching_events = []
    event_type_counts = {}
    
    for event in all_events:
        event_data = event.to_dict()
        
        # Check if this event belongs to our campaign
        email_data = event_data.get('email_data', {})
        event_campaign_id = email_data.get('campaign_id')
        
        if event_campaign_id == campaign_id:
            matching_events.append(event_data)
            event_type = event_data.get('event_type', 'unknown')
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
    
    print(f"\n  ✓ Found {len(matching_events)} events for this campaign")
    
    if matching_events:
        print("\n  Event type breakdown:")
        for event_type, count in sorted(event_type_counts.items()):
            print(f"    - {event_type}: {count}")
        
        print("\n  Sample matching events (first 2):")
        for i, event_data in enumerate(matching_events[:2], 1):
            print(f"\n  Matching Event {i}:")
            print(f"    - event_type: {event_data.get('event_type')}")
            print(f"    - campaign_id in email_data: {event_data.get('email_data', {}).get('campaign_id')}")
            print(f"    - email: {event_data.get('email_data', {}).get('email_address')}")
    else:
        # Let's check if the campaign_id might be stored differently
        print("\n  ⚠️  No events found with matching campaign_id")
        print("\n  Checking different field locations...")
        
        for event in all_events[:10]:
            event_data = event.to_dict()
            
            # Check top-level campaign_id
            if 'campaign_id' in event_data:
                print(f"\n  Found top-level campaign_id: {event_data.get('campaign_id')}")
            
            # Check nested locations
            for key in ['email_data', 'data', 'metadata']:
                if key in event_data and isinstance(event_data[key], dict):
                    if 'campaign_id' in event_data[key]:
                        print(f"\n  Found campaign_id in {key}: {event_data[key].get('campaign_id')}")

if not campaign_found:
    print("\n❌ Campaign 'test15' not found in Firestore")
    
    # List all campaigns
    print("\n4. LISTING ALL CAMPAIGNS...")
    all_campaigns = list(db.collection('campaigns').limit(10).stream())
    print(f"\n  Found {len(all_campaigns)} campaigns:")
    for camp in all_campaigns:
        camp_data = camp.to_dict()
        print(f"    - {camp.id}: {camp_data.get('name')} (status: {camp_data.get('status')})")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)