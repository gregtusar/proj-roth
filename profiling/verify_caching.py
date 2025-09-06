#!/usr/bin/env python3
"""
Verify BigQuery caching with a simple, fast query
"""

import time
from google.cloud import bigquery

def verify_caching():
    client = bigquery.Client(project="proj-roth")
    
    # Very simple query that should cache well
    query = "SELECT COUNT(*) as total FROM `proj-roth.voter_data.voters`"
    
    print("🔍 Verifying BigQuery Cache with Simple Query")
    print("=" * 60)
    
    # Run 1: Force no cache
    print("\nRun 1: Without cache (forced)")
    job_config = bigquery.QueryJobConfig()
    job_config.use_query_cache = False
    
    start = time.time()
    job1 = client.query(query, job_config=job_config)
    result1 = list(job1.result())
    time1 = (time.time() - start) * 1000
    
    print(f"  Time: {time1:.2f}ms")
    print(f"  Bytes: {job1.total_bytes_processed:,}")
    print(f"  Cache hit: {job1.cache_hit}")
    print(f"  Result: {result1[0]['total']:,} voters")
    
    # Run 2: Allow cache
    print("\nRun 2: With cache enabled")
    job_config2 = bigquery.QueryJobConfig()
    job_config2.use_query_cache = True
    
    start = time.time()
    job2 = client.query(query, job_config=job_config2)
    result2 = list(job2.result())
    time2 = (time.time() - start) * 1000
    
    print(f"  Time: {time2:.2f}ms")
    print(f"  Bytes: {job2.total_bytes_processed:,}")
    print(f"  Cache hit: {job2.cache_hit}")
    
    # Run 3: Should definitely be cached now
    print("\nRun 3: Should be cached")
    start = time.time()
    job3 = client.query(query, job_config=job_config2)
    result3 = list(job3.result())
    time3 = (time.time() - start) * 1000
    
    print(f"  Time: {time3:.2f}ms")
    print(f"  Bytes: {job3.total_bytes_processed:,}")
    print(f"  Cache hit: {job3.cache_hit}")
    
    print("\n" + "=" * 60)
    
    if job2.cache_hit or job3.cache_hit:
        print("✅ CACHING IS WORKING!")
        fastest = min(time2, time3)
        savings = ((time1 - fastest) / time1) * 100
        print(f"   Speed improvement: {savings:.1f}%")
        print(f"   Time saved: {(time1 - fastest):.2f}ms")
        
        if job3.cache_hit:
            print(f"   💰 Cost savings: ${(job1.total_bytes_processed / (1024**4)) * 6.25:.6f} saved per cached query")
    else:
        print("⚠️  Cache not hitting - this could be due to:")
        print("   - Query results changing frequently")
        print("   - Cache TTL expired (24 hours)")
        print("   - Different query fingerprint due to whitespace/formatting")
        
    # Test our implementations
    print("\n" + "=" * 60)
    print("TESTING OUR IMPLEMENTATIONS")
    print("=" * 60)
    
    # Test ADK BigQuery tool
    print("\n🔧 Testing ADK BigQuery Tool:")
    from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool
    
    tool = BigQueryReadOnlyTool()
    
    for i in range(3):
        start = time.time()
        result = tool.run("SELECT COUNT(*) FROM `proj-roth.voter_data.voters`")
        elapsed = (time.time() - start) * 1000
        print(f"  Run {i+1}: {elapsed:.2f}ms - {result.get('row_count', 0)} rows")
        
    # Test backend service
    print("\n🚀 Testing Backend Service:")
    import asyncio
    from backend.services.bigquery_service import execute_query
    
    async def test_backend():
        for i in range(3):
            start = time.time()
            result = await execute_query("SELECT COUNT(*) FROM `proj-roth.voter_data.voters`")
            elapsed = (time.time() - start) * 1000
            print(f"  Run {i+1}: {elapsed:.2f}ms - {result['total_rows']} rows")
    
    asyncio.run(test_backend())
    
    print("\n✨ Cache verification complete!")

if __name__ == "__main__":
    verify_caching()