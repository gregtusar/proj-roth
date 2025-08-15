import os
from google.cloud import storage

def test_gcp_access():
    """Test GCP bucket access with current credentials."""
    
    try:
        client = storage.Client(project='proj-roth')
        
        print("✅ Successfully initialized GCP client")
        
        print("🔍 Attempting to list buckets...")
        buckets = list(client.list_buckets())
        print(f"📁 Found {len(buckets)} accessible buckets:")
        for bucket in buckets:
            print(f"   - {bucket.name}")
        
        print(f"\n🎯 Attempting to access 'nj7voterfile' bucket...")
        bucket = client.bucket('nj7voterfile')
        
        print("📋 Listing files in bucket...")
        blobs = list(bucket.list_blobs())
        print(f"📄 Found {len(blobs)} files:")
        for blob in blobs:
            size_mb = blob.size / (1024 * 1024) if blob.size else 0
            print(f"   - {blob.name} ({size_mb:.1f} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing GCP: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🔐 Testing GCP bucket access...")
    test_gcp_access()
