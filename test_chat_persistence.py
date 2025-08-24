#!/usr/bin/env python3
"""Test script for chat persistence functionality"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api"

# Test user credentials (you'll need to get a valid token first)
def get_auth_token():
    """Get auth token - you need to implement proper OAuth flow"""
    # For testing, you might need to manually get a token from the browser
    # or implement the full OAuth flow
    print("Please login via the web interface and get a token from localStorage")
    print("Run in browser console: localStorage.getItem('access_token')")
    token = input("Enter token: ").strip()
    return token

def test_session_operations(token):
    """Test session CRUD operations"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n1. Creating a new session...")
    create_response = requests.post(
        f"{API_URL}/sessions/",
        headers=headers,
        json={
            "session_name": f"Test Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "first_message": "Hello, this is a test message"
        }
    )
    
    if create_response.status_code == 200:
        session = create_response.json()
        print(f"✓ Created session: {session['session_id']}")
        print(f"  Name: {session['session_name']}")
        session_id = session['session_id']
    else:
        print(f"✗ Failed to create session: {create_response.status_code}")
        print(create_response.text)
        return
    
    print("\n2. Getting all sessions...")
    list_response = requests.get(f"{API_URL}/sessions/", headers=headers)
    
    if list_response.status_code == 200:
        sessions = list_response.json()['sessions']
        print(f"✓ Found {len(sessions)} sessions")
        for s in sessions[:3]:  # Show first 3
            print(f"  - {s['session_name']} ({s['session_id'][:8]}...)")
    else:
        print(f"✗ Failed to get sessions: {list_response.status_code}")
    
    print("\n3. Getting session messages...")
    messages_response = requests.get(
        f"{API_URL}/sessions/{session_id}",
        headers=headers
    )
    
    if messages_response.status_code == 200:
        data = messages_response.json()
        print(f"✓ Retrieved session with {len(data['messages'])} messages")
    else:
        print(f"✗ Failed to get messages: {messages_response.status_code}")
    
    print("\n4. Renaming session...")
    rename_response = requests.put(
        f"{API_URL}/sessions/{session_id}",
        headers=headers,
        json={"session_name": "Renamed Test Session"}
    )
    
    if rename_response.status_code == 200:
        print("✓ Session renamed successfully")
    else:
        print(f"✗ Failed to rename: {rename_response.status_code}")
    
    print("\n5. Deleting session...")
    delete_response = requests.delete(
        f"{API_URL}/sessions/{session_id}",
        headers=headers
    )
    
    if delete_response.status_code == 200:
        print("✓ Session deleted successfully")
    else:
        print(f"✗ Failed to delete: {delete_response.status_code}")

def main():
    print("Chat Persistence Test Script")
    print("=" * 40)
    
    # Get auth token
    token = get_auth_token()
    
    if not token:
        print("No token provided. Exiting.")
        return
    
    # Run tests
    try:
        test_session_operations(token)
    except Exception as e:
        print(f"\nError during testing: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()