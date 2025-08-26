#!/usr/bin/env python3
"""Test script to check what's in Firestore lists"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from backend.services.firestore_list_service import FirestoreListService

async def main():
    # Initialize service
    service = FirestoreListService()
    
    if not service.connected:
        print("Firestore is not connected")
        return
    
    # Test user ID from the logs
    test_user_id = "116551015281252125032"
    
    print(f"Checking lists for user: {test_user_id}")
    print("-" * 50)
    
    # Get all documents in the collection
    try:
        # Get all documents
        docs = service.lists_collection.stream()
        
        print("All documents in voter_lists collection:")
        async for doc in docs:
            data = doc.to_dict()
            print(f"\nDocument ID: {doc.id}")
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Name: {data.get('name')}")
            print(f"  Created: {data.get('created_at')}")
            print(f"  Updated: {data.get('updated_at')}")
            print(f"  Is Active: {data.get('is_active', 'not set')}")
            
            # Check date types
            if 'updated_at' in data:
                print(f"  Updated type: {type(data['updated_at'])}")
            if 'created_at' in data:
                print(f"  Created type: {type(data['created_at'])}")
                
    except Exception as e:
        print(f"Error reading documents: {e}")
    
    print("\n" + "=" * 50)
    print("Testing get_user_lists method:")
    
    # Test the actual method
    lists = await service.get_user_lists(test_user_id)
    print(f"Found {len(lists)} lists for user")
    
    for lst in lists:
        print(f"\n- {lst.name}")
        print(f"  ID: {lst.id}")
        print(f"  Updated: {lst.updated_at} (type: {type(lst.updated_at)})")
        print(f"  Created: {lst.created_at} (type: {type(lst.created_at)})")

if __name__ == "__main__":
    asyncio.run(main())