import os
from google.cloud import storage
import pandas as pd

def download_voter_data():
    """Download the voter data file from GCP bucket."""
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/dev/stdin'
    
    try:
        client = storage.Client(project='proj-roth')
        
        bucket = client.bucket('nj7voterfile')
        
        blob = bucket.blob('export-20250729.csv')
        
        local_file_path = '/home/ubuntu/export-20250729.csv'
        blob.download_to_filename(local_file_path)
        
        print(f"✅ Successfully downloaded voter data to {local_file_path}")
        
        file_size = os.path.getsize(local_file_path)
        print(f"📁 File size: {file_size / (1024*1024):.1f} MB")
        
        df = pd.read_csv(local_file_path, nrows=5)
        print(f"📊 Data preview - Shape: {df.shape}")
        print("Columns:", list(df.columns))
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading voter data: {e}")
        print("\nThis could be due to:")
        print("- Insufficient permissions on the GCP service account")
        print("- Bucket or file doesn't exist")
        print("- Network connectivity issues")
        return False

if __name__ == "__main__":
    print("🔄 Attempting to download voter data from GCP bucket...")
    download_voter_data()
