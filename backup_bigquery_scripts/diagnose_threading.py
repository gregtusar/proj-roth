#!/usr/bin/env python3
"""
Diagnostic script to analyze threading behavior in ultra_fast_geocoding_pipeline.py
This script helps identify why the pipeline appears to run with only 1 thread.
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'geocoding'))

def test_global_rate_limiter():
    """Test the GlobalRateLimiter to see if it's causing serialization."""
    print("🔍 Testing GlobalRateLimiter behavior...")
    
    try:
        from ultra_fast_geocoding_pipeline import GlobalRateLimiter
        
        rate_limiter = GlobalRateLimiter(50)  # 50 req/sec
        results = Queue()
        
        def worker(worker_id):
            start_time = time.time()
            rate_limiter.acquire()
            end_time = time.time()
            results.put((worker_id, start_time, end_time, threading.current_thread().ident))
        
        print("🚀 Starting 10 threads to test rate limiter contention...")
        start_test = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()
        
        end_test = time.time()
        
        print(f"⏱️  Total test time: {end_test - start_test:.2f} seconds")
        print("📊 Thread execution timeline:")
        
        while not results.empty():
            worker_id, start, end, thread_id = results.get()
            print(f"  Worker {worker_id} (Thread {thread_id}): {start - start_test:.3f}s - {end - start_test:.3f}s")
        
        expected_time = 10 / 50  # 10 requests at 50 req/sec
        if end_test - start_test > expected_time * 2:
            print("❌ ISSUE: Rate limiter is causing excessive serialization")
        else:
            print("✅ Rate limiter appears to be working correctly")
            
    except ImportError as e:
        print(f"❌ Cannot import GlobalRateLimiter: {e}")

def test_threading_without_rate_limit():
    """Test pure threading without rate limiting."""
    print("\n🔍 Testing pure threading without rate limiting...")
    
    def simple_worker(worker_id):
        time.sleep(0.1)  # Simulate work
        return f"Worker {worker_id} completed on thread {threading.current_thread().ident}"
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(simple_worker, i) for i in range(10)]
        results = [future.result() for future in as_completed(futures)]
    
    end_time = time.time()
    
    print(f"⏱️  10 workers completed in {end_time - start_time:.2f} seconds")
    
    unique_threads = set()
    for result in results:
        thread_id = result.split()[-1]
        unique_threads.add(thread_id)
        print(f"  {result}")
    
    print(f"📊 Used {len(unique_threads)} unique threads")
    
    if len(unique_threads) > 1:
        print("✅ Threading is working correctly")
    else:
        print("❌ ISSUE: Only 1 thread was used")

def check_bigquery_client_threading():
    """Check if BigQuery client has threading limitations."""
    print("\n🔍 Checking BigQuery client configuration...")
    
    try:
        from google.cloud import bigquery
        
        client = bigquery.Client()
        print(f"✅ BigQuery client created successfully")
        print(f"📊 Client project: {client.project}")
        
        if hasattr(client, '_http'):
            print(f"📊 HTTP client: {type(client._http)}")
        
    except Exception as e:
        print(f"❌ BigQuery client issue: {e}")

def main():
    """Run all diagnostic tests."""
    print("🔬 Ultra-Fast Geocoding Pipeline Threading Diagnostics")
    print("=" * 60)
    
    test_threading_without_rate_limit()
    test_global_rate_limiter()
    check_bigquery_client_threading()
    
    print("\n📋 DIAGNOSTIC SUMMARY:")
    print("1. If pure threading works but rate limiter doesn't: GlobalRateLimiter is the bottleneck")
    print("2. If neither works: System-level threading issue")
    print("3. Check BigQuery client for connection pool limits")
    print("4. Monitor actual voter count: SELECT COUNT(*) FROM voters WHERE latitude IS NULL")

if __name__ == "__main__":
    main()
