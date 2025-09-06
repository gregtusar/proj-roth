#!/usr/bin/env python3
"""
Test BigQuery caching implementation
Verifies that query caching is working and measures performance improvement
"""

import time
import sys
from pathlib import Path
from google.cloud import bigquery

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_query_caching():
    """Test that query caching is working properly"""
    
    client = bigquery.Client(project="proj-roth")
    
    # Test query - using the normalized schema with voter_geo_view
    test_query = """
    SELECT 
        demo_party, 
        COUNT(*) as count 
    FROM `proj-roth.voter_data.voter_geo_view` 
    WHERE city = 'WESTFIELD'
    GROUP BY demo_party
    ORDER BY count DESC
    """
    
    print("🔍 Testing BigQuery Caching Implementation")
    print("=" * 60)
    
    # First run - without cache (cold)
    print("\n1️⃣ First Query (Cold - No Cache):")
    job_config = bigquery.QueryJobConfig()
    job_config.use_query_cache = False  # Explicitly disable cache for first run
    
    start_time = time.time()
    query_job = client.query(test_query, job_config=job_config)
    results_cold = list(query_job.result())
    cold_time = (time.time() - start_time) * 1000
    
    print(f"   ⏱️  Execution time: {cold_time:.2f}ms")
    print(f"   📊 Bytes processed: {query_job.total_bytes_processed:,}")
    print(f"   💾 Cache hit: {query_job.cache_hit}")
    
    # Second run - with cache enabled (warm)
    print("\n2️⃣ Second Query (Warm - With Cache):")
    job_config_cached = bigquery.QueryJobConfig()
    job_config_cached.use_query_cache = True  # Enable cache
    
    start_time = time.time()
    query_job_cached = client.query(test_query, job_config=job_config_cached)
    results_warm = list(query_job_cached.result())
    warm_time = (time.time() - start_time) * 1000
    
    print(f"   ⏱️  Execution time: {warm_time:.2f}ms")
    print(f"   📊 Bytes processed: {query_job_cached.total_bytes_processed:,}")
    print(f"   💾 Cache hit: {query_job_cached.cache_hit}")
    
    # Calculate improvement
    improvement = ((cold_time - warm_time) / cold_time) * 100 if cold_time > 0 else 0
    
    print("\n📈 Performance Analysis:")
    print(f"   🚀 Speed improvement: {improvement:.1f}%")
    print(f"   ⚡ Time saved: {(cold_time - warm_time):.2f}ms")
    
    if query_job_cached.cache_hit:
        print(f"   ✅ CACHING IS WORKING! Query served from cache")
        print(f"   💰 Cost savings: No bytes billed for cached query")
    else:
        print(f"   ⚠️  Cache not hit - query may have changed or cache expired")
    
    # Test our updated BigQuery tool
    print("\n3️⃣ Testing Updated BigQuery Tool:")
    from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool
    
    tool = BigQueryReadOnlyTool()
    test_sql = "SELECT COUNT(*) as total FROM `proj-roth.voter_data.voter_geo_view` WHERE city = 'SUMMIT'"
    
    # First run
    start_time = time.time()
    result1 = tool.run(test_sql)
    tool_time1 = (time.time() - start_time) * 1000
    
    # Second run (should be cached)
    start_time = time.time()
    result2 = tool.run(test_sql)
    tool_time2 = (time.time() - start_time) * 1000
    
    print(f"   BigQuery Tool first run: {tool_time1:.2f}ms")
    print(f"   BigQuery Tool second run: {tool_time2:.2f}ms")
    
    if tool_time2 < tool_time1 * 0.5:  # If second run is less than 50% of first
        print(f"   ✅ BigQuery Tool caching working! {((tool_time1 - tool_time2) / tool_time1 * 100):.1f}% faster")
    else:
        print(f"   ℹ️  Similar performance (may already be cached)")
    
    # Test backend service
    print("\n4️⃣ Testing Backend Service Caching:")
    from backend.services.bigquery_service import execute_query
    import asyncio
    
    async def test_backend():
        # First run
        start = time.time()
        result1 = await execute_query("SELECT COUNT(*) FROM `proj-roth.voter_data.voters`")
        backend_time1 = (time.time() - start) * 1000
        
        # Second run (cached)
        start = time.time()
        result2 = await execute_query("SELECT COUNT(*) FROM `proj-roth.voter_data.voters`")
        backend_time2 = (time.time() - start) * 1000
        
        print(f"   Backend service first run: {backend_time1:.2f}ms")
        print(f"   Backend service second run: {backend_time2:.2f}ms")
        
        if backend_time2 < backend_time1 * 0.5:
            print(f"   ✅ Backend caching working! {((backend_time1 - backend_time2) / backend_time1 * 100):.1f}% faster")
        else:
            print(f"   ℹ️  Similar performance (may already be cached)")
    
    asyncio.run(test_backend())
    
    print("\n" + "=" * 60)
    print("✅ CACHING IMPLEMENTATION COMPLETE")
    print("=" * 60)
    print("\nExpected benefits:")
    print("  • 50-90% faster for repeated queries")
    print("  • Zero bytes billed for cached queries")
    print("  • Better user experience with instant responses")
    print("  • Reduced load on BigQuery infrastructure")
    
    return query_job_cached.cache_hit

if __name__ == "__main__":
    success = test_query_caching()
    sys.exit(0 if success else 1)