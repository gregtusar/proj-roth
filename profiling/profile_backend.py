#!/usr/bin/env python3
"""
Backend Performance Profiler
Profiles the FastAPI backend and ADK agent for performance bottlenecks.
"""

import asyncio
import cProfile
import pstats
import io
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import tracemalloc
import psutil
import aiohttp
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class BackendProfiler:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": {},
            "memory": {},
            "database": {},
            "agent": {}
        }
        
    async def profile_endpoint(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Profile a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        # CPU profiling
        profiler = cProfile.Profile()
        
        # Memory tracking
        tracemalloc.start()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        profiler.enable()
        start_time = time.perf_counter()
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url) as response:
                        result = await response.json()
                        status = response.status
                elif method == "POST":
                    async with session.post(url, json=data) as response:
                        result = await response.json()
                        status = response.status
                        
        except Exception as e:
            result = {"error": str(e)}
            status = 500
            
        end_time = time.perf_counter()
        profiler.disable()
        
        # Memory after
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        
        return {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "response_time_ms": (end_time - start_time) * 1000,
            "memory_delta_mb": memory_after - memory_before,
            "memory_peak_mb": peak / 1024 / 1024,
            "top_functions": self._extract_top_functions(s.getvalue())
        }
    
    def _extract_top_functions(self, stats_output: str) -> List[Dict]:
        """Extract top functions from pstats output"""
        lines = stats_output.split('\n')
        functions = []
        
        for line in lines[5:15]:  # Skip header, get top 10
            if line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    functions.append({
                        "calls": parts[0],
                        "time": parts[2],
                        "cumulative": parts[3],
                        "function": ' '.join(parts[5:])
                    })
        
        return functions
    
    async def profile_agent_query(self, query: str) -> Dict:
        """Profile ADK agent query performance"""
        start_time = time.perf_counter()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = await self.profile_endpoint(
            "POST", 
            "/api/agent/query",
            {"query": query}
        )
        
        end_time = time.perf_counter()
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            "query": query,
            "total_time_ms": (end_time - start_time) * 1000,
            "memory_used_mb": memory_after - memory_before,
            **result
        }
    
    async def profile_bigquery_operations(self) -> Dict:
        """Profile BigQuery operations"""
        queries = [
            "SELECT COUNT(*) FROM `proj-roth.voter_data.voters`",
            "SELECT * FROM `proj-roth.voter_data.voters` LIMIT 100",
            "SELECT demo_party, COUNT(*) as count FROM `proj-roth.voter_data.voters` GROUP BY demo_party",
            "SELECT * FROM `proj-roth.voter_data.voters` WHERE city = 'WESTFIELD' LIMIT 1000"
        ]
        
        results = []
        for query in queries:
            start = time.perf_counter()
            result = await self.profile_endpoint(
                "POST",
                "/api/query",
                {"query": query}
            )
            result["query"] = query[:50] + "..." if len(query) > 50 else query
            results.append(result)
            
        return {"queries": results}
    
    async def profile_websocket_connection(self) -> Dict:
        """Profile WebSocket connection and message handling"""
        import socketio
        
        sio = socketio.AsyncClient()
        metrics = {
            "connection_time_ms": 0,
            "message_latencies": [],
            "memory_usage": []
        }
        
        start = time.perf_counter()
        
        try:
            await sio.connect(self.base_url)
            metrics["connection_time_ms"] = (time.perf_counter() - start) * 1000
            
            # Test message latency
            for i in range(10):
                msg_start = time.perf_counter()
                await sio.emit("test_message", {"index": i})
                await asyncio.sleep(0.1)
                metrics["message_latencies"].append((time.perf_counter() - msg_start) * 1000)
                metrics["memory_usage"].append(psutil.Process().memory_info().rss / 1024 / 1024)
                
            await sio.disconnect()
            
        except Exception as e:
            metrics["error"] = str(e)
            
        return metrics
    
    async def run_full_profile(self):
        """Run complete profiling suite"""
        print("🔍 Starting Backend Performance Profiling...")
        
        # Profile main endpoints
        print("\n📍 Profiling API Endpoints...")
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/auth/me"),
            ("GET", "/api/sessions"),
            ("GET", "/api/lists"),
            ("POST", "/api/chat/send", {"message": "Hello"})
        ]
        
        for method, endpoint, *data in endpoints:
            print(f"  - {method} {endpoint}")
            result = await self.profile_endpoint(method, endpoint, data[0] if data else None)
            self.results["endpoints"][endpoint] = result
            
        # Profile agent queries
        print("\n🤖 Profiling ADK Agent...")
        agent_queries = [
            "How many voters are registered?",
            "Show me voters in Westfield",
            "What are the party demographics?"
        ]
        
        for query in agent_queries:
            print(f"  - Query: {query[:50]}...")
            result = await self.profile_agent_query(query)
            self.results["agent"][query] = result
            
        # Profile BigQuery
        print("\n🗄️ Profiling BigQuery Operations...")
        self.results["database"] = await self.profile_bigquery_operations()
        
        # Profile WebSocket
        print("\n🔌 Profiling WebSocket...")
        self.results["websocket"] = await self.profile_websocket_connection()
        
        # Generate report
        self._generate_report()
        
    def _generate_report(self):
        """Generate profiling report"""
        report_path = Path(__file__).parent / f"backend_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n✅ Profile report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        # Endpoint performance
        print("\n📊 API Endpoint Performance:")
        for endpoint, data in self.results["endpoints"].items():
            print(f"  {endpoint}: {data.get('response_time_ms', 0):.2f}ms")
            
        # Agent performance
        if self.results["agent"]:
            print("\n🤖 Agent Query Performance:")
            for query, data in self.results["agent"].items():
                print(f"  {query[:30]}...: {data.get('total_time_ms', 0):.2f}ms")
                
        # Database performance
        if "queries" in self.results["database"]:
            print("\n🗄️ BigQuery Performance:")
            for query_data in self.results["database"]["queries"]:
                print(f"  {query_data['query']}: {query_data.get('response_time_ms', 0):.2f}ms")
                
        # Identify bottlenecks
        print("\n⚠️ Potential Bottlenecks:")
        slow_endpoints = [
            (ep, data['response_time_ms']) 
            for ep, data in self.results["endpoints"].items() 
            if data.get('response_time_ms', 0) > 100
        ]
        
        if slow_endpoints:
            for ep, time_ms in sorted(slow_endpoints, key=lambda x: x[1], reverse=True):
                print(f"  - {ep}: {time_ms:.2f}ms (>100ms)")
        else:
            print("  None identified (all endpoints <100ms)")

if __name__ == "__main__":
    print("="*60)
    print("NJ VOTER CHAT - BACKEND PERFORMANCE PROFILER")
    print("="*60)
    print("\n⚠️  Make sure the backend is running on localhost:8080")
    print("   Run: python backend/main.py")
    print()
    
    input("Press Enter to start profiling...")
    
    profiler = BackendProfiler()
    asyncio.run(profiler.run_full_profile())