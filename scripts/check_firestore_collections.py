#!/usr/bin/env python3
"""Check which Firestore collections exist in the project."""

import os
import sys
from google.cloud import firestore

def check_collections():
    """Check and list all Firestore collections."""
    
    # Set project ID
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
    print(f"Checking Firestore collections for project: {project_id}")
    print("-" * 50)
    
    # Initialize Firestore client
    client = firestore.Client(project=project_id)
    
    # Collections we expect based on the code
    expected_collections = [
        'chat_sessions',    # For chat session management
        'chat_messages',    # For chat message storage
        'voter_lists'       # For saved voter lists
    ]
    
    print("Expected collections based on code:")
    for coll in expected_collections:
        print(f"  - {coll}")
    print()
    
    print("Checking actual collections in Firestore:")
    print("-" * 50)
    
    # Get all collections
    try:
        collections = client.collections()
        found_collections = []
        
        for collection in collections:
            collection_id = collection.id
            found_collections.append(collection_id)
            
            # Count documents in each collection
            docs = collection.limit(1).stream()
            doc_count = 0
            for doc in docs:
                doc_count = 1  # At least one exists
                # Try to get a rough count (limited for performance)
                all_docs = collection.limit(100).stream()
                doc_count = sum(1 for _ in all_docs)
                break
            
            status = "✓" if collection_id in expected_collections else "?"
            print(f"{status} {collection_id}: {doc_count}+ documents")
        
        print()
        print("Summary:")
        print("-" * 50)
        
        # Check for missing collections
        missing = set(expected_collections) - set(found_collections)
        if missing:
            print(f"⚠️  Missing collections that need to be created:")
            for coll in missing:
                print(f"   - {coll}")
        else:
            print("✅ All expected collections exist!")
        
        # Check for unexpected collections
        unexpected = set(found_collections) - set(expected_collections)
        if unexpected:
            print(f"\nℹ️  Additional collections found:")
            for coll in unexpected:
                print(f"   - {coll}")
    
    except Exception as e:
        print(f"Error accessing Firestore: {e}")
        print("\nNote: Firestore collections are created automatically when the first document is added.")
        print("If this is a new deployment, the collections will be created when users start using the app.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(check_collections())