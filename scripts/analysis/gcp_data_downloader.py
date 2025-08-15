import os
import tempfile
import json
import pandas as pd
from google.cloud import storage

class GCPVoterDataDownloader:
    """Utility for downloading voter data from GCP bucket with secure credential handling."""
    
    def __init__(self, project_id='proj-roth', bucket_name='nj7voterfile'):
        """Initialize the downloader with GCP project and bucket details."""
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client = None
        
    def setup_credentials_from_json(self, credentials_json):
        """Set up GCP client using provided JSON credentials."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(credentials_json)
            creds_file_path = f.name
        
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file_path
            self.client = storage.Client(project=self.project_id)
            print(f"✅ Successfully initialized GCP client for project: {self.project_id}")
            return True
        except Exception as e:
            print(f"❌ Error setting up credentials: {e}")
            return False
        finally:
            try:
                os.unlink(creds_file_path)
            except:
                pass
    
    def setup_credentials_from_file(self, credentials_file_path):
        """Set up GCP client using credentials file path."""
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file_path
            self.client = storage.Client(project=self.project_id)
            print(f"✅ Successfully initialized GCP client for project: {self.project_id}")
            return True
        except Exception as e:
            print(f"❌ Error setting up credentials: {e}")
            return False
    
    def list_bucket_contents(self):
        """List all files in the configured bucket."""
        if not self.client:
            print("❌ GCP client not initialized. Please set up credentials first.")
            return None
        
        try:
            print(f"📋 Listing contents of bucket: {self.bucket_name}")
            bucket = self.client.bucket(self.bucket_name)
            blobs = list(bucket.list_blobs())
            
            print(f"📄 Found {len(blobs)} files:")
            for blob in blobs:
                size_mb = blob.size / (1024 * 1024) if blob.size else 0
                print(f"   - {blob.name} ({size_mb:.1f} MB)")
            
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"❌ Error listing bucket contents: {e}")
            return None
    
    def download_file(self, file_name, local_path=None):
        """Download a specific file from the bucket."""
        if not self.client:
            print("❌ GCP client not initialized. Please set up credentials first.")
            return False
        
        if local_path is None:
            local_path = f"./{file_name}"
        
        try:
            print(f"⬇️  Downloading {file_name} from {self.bucket_name}...")
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(file_name)
            
            blob.download_to_filename(local_path)
            
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print(f"✅ Successfully downloaded {file_name}")
                print(f"📁 File size: {file_size / (1024*1024):.1f} MB")
                print(f"📍 Location: {local_path}")
                return True
            else:
                print("❌ Download failed - file not found locally")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            return False
    
    def download_voter_data(self, file_name='export-20250729.csv', local_path=None):
        """Download the voter data file and provide a quick preview."""
        if self.download_file(file_name, local_path):
            try:
                actual_path = local_path if local_path else f"./{file_name}"
                print(f"\n📊 Data Preview:")
                df_preview = pd.read_csv(actual_path, nrows=5)
                print(f"Shape (first 5 rows): {df_preview.shape}")
                print(f"Columns: {len(df_preview.columns)}")
                print(f"Sample columns: {list(df_preview.columns[:10])}")
                return True
            except Exception as e:
                print(f"Could not preview data: {e}")
                return True
        return False

def main():
    """Example usage of the GCP voter data downloader."""
    print("🗳️  GCP VOTER DATA DOWNLOADER")
    print("=" * 40)
    
    downloader = GCPVoterDataDownloader()
    
    print("\nTo use this downloader:")
    print("1. Set up credentials using setup_credentials_from_json() or setup_credentials_from_file()")
    print("2. List bucket contents with list_bucket_contents()")
    print("3. Download files with download_file() or download_voter_data()")
    
    print("\nExample:")
    print("downloader = GCPVoterDataDownloader()")
    print("downloader.setup_credentials_from_file('/path/to/credentials.json')")
    print("downloader.download_voter_data('export-20250729.csv', './voter_data.csv')")

if __name__ == "__main__":
    main()
