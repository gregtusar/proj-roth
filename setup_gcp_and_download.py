import os
import tempfile
import json
from google.cloud import storage

def setup_credentials_and_download():
    """Set up GCP credentials and download the voter data file."""
    
    creds_json = os.environ.get('gcp_credentials')
    if not creds_json:
        print("❌ No GCP credentials found in environment variable")
        return False
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(creds_json)
        creds_file_path = f.name
    
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file_path
        
        print("🔐 Setting up GCP client...")
        client = storage.Client(project='proj-roth')
        
        print("✅ Successfully initialized GCP client")
        
        print("🎯 Accessing 'nj7voterfile' bucket...")
        bucket = client.bucket('nj7voterfile')
        
        print("📋 Listing files in bucket...")
        blobs = list(bucket.list_blobs())
        print(f"📄 Found {len(blobs)} files:")
        for blob in blobs:
            size_mb = blob.size / (1024 * 1024) if blob.size else 0
            print(f"   - {blob.name} ({size_mb:.1f} MB)")
        
        target_file = 'export-20250729.csv'
        local_path = f'/home/ubuntu/{target_file}'
        
        print(f"\n⬇️  Downloading {target_file}...")
        blob = bucket.blob(target_file)
        blob.download_to_filename(local_path)
        
        if os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            print(f"✅ Successfully downloaded {target_file}")
            print(f"📁 File size: {file_size / (1024*1024):.1f} MB")
            print(f"📍 Location: {local_path}")
            return True
        else:
            print("❌ Download failed - file not found locally")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False
    
    finally:
        try:
            os.unlink(creds_file_path)
        except:
            pass

if __name__ == "__main__":
    print("🗳️  GCP VOTER DATA DOWNLOAD")
    print("=" * 40)
    setup_credentials_and_download()
