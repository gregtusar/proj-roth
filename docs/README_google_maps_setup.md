# Google Maps API Setup for Optimized Geocoding

## Prerequisites

1. **Google Cloud Project with Billing Enabled**
   - Ensure your Google Cloud project has billing enabled
   - Estimated cost for 622K voters: ~$2,500-3,100

2. **Enable Google Maps Geocoding API**
   ```bash
   # Using gcloud CLI
   gcloud services enable geocoding-backend.googleapis.com
   ```

3. **Create API Key**
   - Go to Google Cloud Console → APIs & Credentials → Credentials
   - Click "Create Credentials" → "API Key"
   - Restrict the key to Geocoding API for security

4. **Set Environment Variable**
   ```bash
   export GOOGLE_MAPS_API_KEY='your_api_key_here'
   ```

## Usage

### Test Google Maps API Setup
```bash
python test_google_maps_geocoding.py
```

### Run Optimized Geocoding Pipeline
```bash
export GOOGLE_MAPS_API_KEY='your_api_key_here'
python optimized_geocoding_pipeline.py
```

## Performance Improvements

- **Rate Limit**: Increased from 10 to 45 requests/second
- **Batch Size**: Increased from 50 to 200 voters per batch
- **Parallel Workers**: Increased from 5 to 15 workers
- **Delays**: Reduced from 2 seconds to 0.5 seconds between batches
- **Expected Speed**: 15-20x faster than previous configuration

## Cost Estimation

- Google Maps Geocoding API: $5.00 per 1,000 requests (first 100K)
- For 622,304 voters: approximately $2,500-3,100 total
- Rate: ~45 requests/second = ~162,000 requests/hour
- Completion time: ~4-6 hours for full dataset
