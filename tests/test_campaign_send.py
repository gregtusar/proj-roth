#!/usr/bin/env python3
"""
Test script to verify campaign email sending functionality
Tests the complete pipeline from list query to SendGrid API
"""
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.firestore_campaign_service import get_firestore_campaign_service
from backend.services.firestore_list_service import get_firestore_list_service
from backend.campaigns import CampaignManager

async def test_campaign_send():
    """Test the campaign send functionality end-to-end"""
    
    print("🧪 Testing Campaign Email Send Pipeline")
    print("=" * 60)
    
    # Initialize services
    campaign_service = get_firestore_campaign_service()
    list_service = get_firestore_list_service()
    campaign_manager = CampaignManager()
    
    # Test user details
    test_user_id = "test_user_123"
    test_user_email = "test@example.com"
    
    print("\n1️⃣ Creating test list with voters who have emails...")
    
    # Create a test list with a query that finds voters with emails
    test_list = await list_service.create_list(
        user_id=test_user_id,
        user_email=test_user_email,
        name="Test List - Voters with Emails",
        description="Test list for campaign email testing",
        query="""
        SELECT master_id, demo_party, municipal_name as city
        FROM `proj-roth.voter_data.voters`
        WHERE email IS NOT NULL
        AND municipal_name = 'WESTFIELD'
        LIMIT 5
        """,
        row_count=5
    )
    
    print(f"   ✅ Created list: {test_list.id}")
    print(f"   List name: {test_list.name}")
    
    print("\n2️⃣ Creating test campaign...")
    
    # Create a test campaign
    test_campaign = await campaign_service.create_campaign(
        user_id=test_user_id,
        user_email=test_user_email,
        name="Test Campaign - " + datetime.now().strftime("%Y%m%d_%H%M%S"),
        subject="Test Email Subject",
        from_name="Test Sender",
        from_email="test@example.com",
        google_doc_id="test_doc_123",  # This will fail with 403 unless shared
        template_id="d-example123",  # Replace with actual SendGrid template ID
        list_id=test_list.id
    )
    
    print(f"   ✅ Created campaign: {test_campaign.id}")
    print(f"   Campaign name: {test_campaign.name}")
    
    print("\n3️⃣ Testing campaign send (dry run)...")
    
    # Test the send functionality
    try:
        # First, let's test getting recipients
        print("\n   📋 Getting list recipients...")
        recipients = await campaign_manager.get_list_recipients(test_list.id, test_user_id)
        
        if recipients:
            print(f"   ✅ Found {len(recipients)} recipients with emails")
            for i, recipient in enumerate(recipients[:3], 1):
                print(f"      {i}. {recipient.get('first_name', 'N/A')} {recipient.get('last_name', 'N/A')} - {recipient.get('email', 'N/A')}")
        else:
            print("   ⚠️ No recipients found with email addresses")
            
        # Test send (will fail if Google Doc not shared or SendGrid not configured)
        print("\n   📧 Testing send campaign...")
        result = await campaign_manager.send_campaign(test_campaign.id, test_user_id)
        
        if result['success']:
            print(f"   ✅ Campaign send successful!")
            print(f"      Sent: {result.get('sent_count', 0)} emails")
            print(f"      Failed: {result.get('failed_count', 0)} emails")
        else:
            print(f"   ❌ Campaign send failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during campaign send: {str(e)}")
    
    print("\n4️⃣ Cleaning up test data...")
    
    # Clean up
    await list_service.delete_list(test_list.id, test_user_id)
    await campaign_service.delete_campaign(test_campaign.id, test_user_id)
    
    print("   ✅ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("✨ Test complete!")
    print("\n📝 Notes:")
    print("   - If Google Doc 403 error: Share doc with nj-voter-chat-app@proj-roth.iam.gserviceaccount.com")
    print("   - If SendGrid fails: Check SENDGRID_API_KEY environment variable")
    print("   - Check logs at: gcloud logging read 'resource.type=cloud_run_revision'")

if __name__ == "__main__":
    asyncio.run(test_campaign_send())