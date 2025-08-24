#!/usr/bin/env python3
"""
Script to clear all chat and list data from both Firestore and BigQuery
"""
import asyncio
from google.cloud import firestore
from google.cloud import bigquery
import os

# Set project ID
PROJECT_ID = "proj-roth"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID

async def clear_firestore():
    """Clear all data from Firestore collections"""
    print("Clearing Firestore data...")
    
    try:
        # Initialize Firestore client
        db = firestore.Client(project=PROJECT_ID)
        
        # Clear chat_sessions collection
        print("  Deleting chat_sessions...")
        sessions_ref = db.collection('chat_sessions')
        batch = db.batch()
        count = 0
        
        for doc in sessions_ref.stream():
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
                print(f"    Deleted {count} sessions...")
        
        if count % 500 != 0:
            batch.commit()
        print(f"  ✓ Deleted {count} chat sessions")
        
        # Clear chat_messages collection
        print("  Deleting chat_messages...")
        messages_ref = db.collection('chat_messages')
        batch = db.batch()
        count = 0
        
        for doc in messages_ref.stream():
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
                print(f"    Deleted {count} messages...")
        
        if count % 500 != 0:
            batch.commit()
        print(f"  ✓ Deleted {count} chat messages")
        
        # Clear voter_lists collection
        print("  Deleting voter_lists...")
        lists_ref = db.collection('voter_lists')
        batch = db.batch()
        count = 0
        
        for doc in lists_ref.stream():
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
                print(f"    Deleted {count} lists...")
        
        if count % 500 != 0:
            batch.commit()
        print(f"  ✓ Deleted {count} voter lists")
        
        print("✓ Firestore data cleared successfully\n")
        
    except Exception as e:
        print(f"✗ Error clearing Firestore: {e}\n")

def clear_bigquery():
    """Clear all data from BigQuery tables"""
    print("Clearing BigQuery data...")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT_ID)
        
        # Tables to clear
        tables_to_clear = [
            "proj-roth.voter_data.chat_sessions",
            "proj-roth.voter_data.voter_lists",
            "proj-roth.voter_data.prompt_history"  # In case it exists
        ]
        
        for table_id in tables_to_clear:
            try:
                # Delete all rows from table
                query = f"DELETE FROM `{table_id}` WHERE TRUE"
                query_job = client.query(query)
                query_job.result()  # Wait for query to complete
                print(f"  ✓ Cleared {table_id}")
            except Exception as e:
                if "Not found" in str(e):
                    print(f"  - Table {table_id} not found (skipping)")
                else:
                    print(f"  ✗ Error clearing {table_id}: {e}")
        
        print("✓ BigQuery data cleared successfully\n")
        
    except Exception as e:
        print(f"✗ Error with BigQuery: {e}\n")

async def main():
    """Main function to clear all data"""
    print("=" * 50)
    print("CLEARING ALL CHAT AND LIST DATA")
    print("=" * 50)
    print()
    
    # Clear Firestore
    await clear_firestore()
    
    # Clear BigQuery
    clear_bigquery()
    
    print("=" * 50)
    print("ALL DATA CLEARED SUCCESSFULLY")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())