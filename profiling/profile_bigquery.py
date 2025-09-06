#!/usr/bin/env python3
"""
BigQuery Performance Profiler
Analyzes query performance, optimization opportunities, and data access patterns.
"""

import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class BigQueryProfiler:
    def __init__(self):
        self.client = bigquery.Client(project="proj-roth")
        self.dataset_id = "voter_data"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "queries": [],
            "indexes": {},
            "partitioning": {},
            "recommendations": []
        }
        
    def profile_table_stats(self, table_name: str) -> Dict:
        """Get table statistics and metadata"""
        table_ref = f"proj-roth.{self.dataset_id}.{table_name}"
        
        try:
            table = self.client.get_table(table_ref)
            
            # Get row count and size
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                SUM(LENGTH(TO_JSON_STRING(t))) as approx_size_bytes
            FROM `{table_ref}` t
            """
            
            result = list(self.client.query(query).result())
            row = result[0] if result else {}
            
            return {
                "table_name": table_name,
                "row_count": row.get("row_count", 0),
                "size_bytes": table.num_bytes,
                "size_mb": table.num_bytes / (1024 * 1024) if table.num_bytes else 0,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "schema_fields": len(table.schema),
                "partitioned": table.time_partitioning is not None,
                "clustered": table.clustering_fields is not None,
                "clustering_fields": table.clustering_fields or []
            }
            
        except Exception as e:
            return {"table_name": table_name, "error": str(e)}
    
    def profile_query_performance(self, query: str, description: str = "") -> Dict:
        """Profile a specific query's performance"""
        
        # Dry run to get query stats
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        
        try:
            dry_run_job = self.client.query(query, job_config=job_config)
            bytes_processed = dry_run_job.total_bytes_processed
            
            # Actual run with timing
            start_time = time.perf_counter()
            job_config = bigquery.QueryJobConfig(use_query_cache=False)
            query_job = self.client.query(query, job_config=job_config)
            
            # Get first row to measure time to first byte
            iterator = query_job.result()
            first_row_time = time.perf_counter()
            
            # Get all results
            results = list(iterator)
            end_time = time.perf_counter()
            
            return {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "description": description,
                "bytes_processed": bytes_processed,
                "bytes_processed_mb": bytes_processed / (1024 * 1024),
                "time_to_first_row_ms": (first_row_time - start_time) * 1000,
                "total_time_ms": (end_time - start_time) * 1000,
                "row_count": len(results),
                "slot_millis": query_job.slot_millis if hasattr(query_job, 'slot_millis') else None,
                "cache_hit": query_job.cache_hit if hasattr(query_job, 'cache_hit') else False,
                "estimated_cost_usd": (bytes_processed / (1024**4)) * 6.25  # $6.25 per TB
            }
            
        except Exception as e:
            return {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "description": description,
                "error": str(e)
            }
    
    def analyze_query_patterns(self) -> List[Dict]:
        """Analyze common query patterns and their performance"""
        
        test_queries = [
            {
                "query": "SELECT COUNT(*) FROM `proj-roth.voter_data.voters`",
                "description": "Simple count",
                "optimization": "Consider using APPROX_COUNT_DISTINCT for large tables"
            },
            {
                "query": """
                    SELECT demo_party, COUNT(*) as count 
                    FROM `proj-roth.voter_data.voters` 
                    GROUP BY demo_party
                """,
                "description": "Party distribution aggregation",
                "optimization": "Consider materialized view for frequently used aggregations"
            },
            {
                "query": """
                    SELECT * FROM `proj-roth.voter_data.voters` 
                    WHERE city = 'WESTFIELD' 
                    LIMIT 1000
                """,
                "description": "City-based filtering",
                "optimization": "Consider clustering by city for better performance"
            },
            {
                "query": """
                    SELECT v.*, s.total_voters, s.dem_voters, s.rep_voters
                    FROM `proj-roth.voter_data.voters` v
                    LEFT JOIN `proj-roth.voter_data.street_party_summary` s
                    ON v.addr_residential_line1 = s.street_address
                    WHERE v.city = 'WESTFIELD'
                    LIMIT 100
                """,
                "description": "Join with summary table",
                "optimization": "Consider denormalizing frequently joined data"
            },
            {
                "query": """
                    SELECT city, 
                           COUNT(*) as total,
                           COUNT(CASE WHEN demo_party = 'DEM' THEN 1 END) as democrats,
                           COUNT(CASE WHEN demo_party = 'REP' THEN 1 END) as republicans
                    FROM `proj-roth.voter_data.voters`
                    GROUP BY city
                    ORDER BY total DESC
                    LIMIT 20
                """,
                "description": "City demographics with conditional aggregation",
                "optimization": "Use COUNTIF instead of COUNT(CASE) for better readability"
            },
            {
                "query": """
                    SELECT *
                    FROM `proj-roth.voter_data.voters`
                    WHERE ST_DWITHIN(
                        location,
                        ST_GEOGPOINT(-74.3473, 40.6509),
                        1000
                    )
                    LIMIT 100
                """,
                "description": "Geospatial proximity search",
                "optimization": "Consider spatial indexing with S2 cells for large-scale geo queries"
            }
        ]
        
        results = []
        for test_query in test_queries:
            print(f"  Testing: {test_query['description']}")
            result = self.profile_query_performance(
                test_query["query"],
                test_query["description"]
            )
            result["optimization"] = test_query["optimization"]
            results.append(result)
            
        return results
    
    def check_index_usage(self) -> Dict:
        """Check if indexes are being used effectively"""
        
        # Query to find most common filter columns
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM `proj-roth.voter_data.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'voters'
        ORDER BY ordinal_position
        """
        
        try:
            results = list(self.client.query(query).result())
            
            # Identify good index candidates
            index_candidates = []
            for row in results:
                if row.column_name in ['city', 'demo_party', 'county', 'zip']:
                    index_candidates.append({
                        "column": row.column_name,
                        "data_type": row.data_type,
                        "reason": "High cardinality filter column"
                    })
                    
            return {
                "total_columns": len(results),
                "index_candidates": index_candidates
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_data_skew(self) -> Dict:
        """Analyze data distribution for optimization opportunities"""
        
        analyses = {}
        
        # Party distribution
        query = """
        SELECT 
            demo_party,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM `proj-roth.voter_data.voters`
        GROUP BY demo_party
        ORDER BY count DESC
        """
        
        try:
            results = list(self.client.query(query).result())
            analyses["party_distribution"] = [
                {"party": row.demo_party, "count": row.count, "percentage": row.percentage}
                for row in results
            ]
        except:
            pass
            
        # City distribution (top 10)
        query = """
        SELECT 
            city,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM `proj-roth.voter_data.voters`
        GROUP BY city
        ORDER BY count DESC
        LIMIT 10
        """
        
        try:
            results = list(self.client.query(query).result())
            analyses["city_distribution"] = [
                {"city": row.city, "count": row.count, "percentage": row.percentage}
                for row in results
            ]
        except:
            pass
            
        return analyses
    
    def generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on profiling"""
        
        recommendations = []
        
        # Check query performance
        slow_queries = [
            q for q in self.results["queries"] 
            if q.get("total_time_ms", 0) > 1000
        ]
        
        if slow_queries:
            recommendations.append(
                f"⚠️ Found {len(slow_queries)} queries taking >1 second. "
                "Consider query optimization or materialized views."
            )
            
        # Check bytes processed
        expensive_queries = [
            q for q in self.results["queries"]
            if q.get("bytes_processed_mb", 0) > 100
        ]
        
        if expensive_queries:
            recommendations.append(
                f"💰 Found {len(expensive_queries)} queries processing >100MB. "
                "Consider adding WHERE clauses or using partitioning."
            )
            
        # Check for clustering opportunities
        if self.results.get("tables", {}).get("voters", {}).get("clustered") is False:
            recommendations.append(
                "🎯 Table 'voters' is not clustered. Consider clustering by "
                "frequently filtered columns like city, demo_party."
            )
            
        # Check for caching opportunities
        non_cached = [
            q for q in self.results["queries"]
            if not q.get("cache_hit", False)
        ]
        
        if len(non_cached) > len(self.results["queries"]) * 0.5:
            recommendations.append(
                "💾 Low cache hit rate. Consider enabling query caching "
                "for frequently run queries."
            )
            
        return recommendations
    
    def run_full_profile(self):
        """Run complete BigQuery profiling"""
        
        print("🔍 Starting BigQuery Performance Profiling...")
        
        # Profile tables
        print("\n📊 Profiling Tables...")
        tables = ["voters", "street_party_summary", "donations"]
        
        for table in tables:
            print(f"  - {table}")
            self.results["tables"][table] = self.profile_table_stats(table)
            
        # Profile queries
        print("\n⚡ Profiling Query Patterns...")
        self.results["queries"] = self.analyze_query_patterns()
        
        # Check indexes
        print("\n🔍 Analyzing Index Usage...")
        self.results["indexes"] = self.check_index_usage()
        
        # Analyze data distribution
        print("\n📈 Analyzing Data Distribution...")
        self.results["data_distribution"] = self.analyze_data_skew()
        
        # Generate recommendations
        self.results["recommendations"] = self.generate_recommendations()
        
        # Save report
        self._generate_report()
        
    def _generate_report(self):
        """Generate and save profiling report"""
        
        report_path = Path(__file__).parent / f"bigquery_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n✅ Profile report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("BIGQUERY PERFORMANCE SUMMARY")
        print("="*60)
        
        # Table stats
        print("\n📊 Table Statistics:")
        for table_name, stats in self.results["tables"].items():
            if "error" not in stats:
                print(f"  {table_name}:")
                print(f"    - Rows: {stats.get('row_count', 0):,}")
                print(f"    - Size: {stats.get('size_mb', 0):.2f} MB")
                print(f"    - Clustered: {stats.get('clustered', False)}")
                
        # Query performance
        print("\n⚡ Query Performance:")
        for query in self.results["queries"]:
            if "error" not in query:
                print(f"  {query['description']}:")
                print(f"    - Time: {query.get('total_time_ms', 0):.2f}ms")
                print(f"    - Data: {query.get('bytes_processed_mb', 0):.2f}MB")
                print(f"    - Cost: ${query.get('estimated_cost_usd', 0):.6f}")
                
        # Recommendations
        if self.results["recommendations"]:
            print("\n💡 Optimization Recommendations:")
            for rec in self.results["recommendations"]:
                print(f"  {rec}")
        
        # Data distribution insights
        if "data_distribution" in self.results:
            print("\n📈 Data Distribution Insights:")
            
            if "party_distribution" in self.results["data_distribution"]:
                print("  Party Distribution:")
                for party in self.results["data_distribution"]["party_distribution"][:5]:
                    print(f"    - {party['party']}: {party['percentage']}%")
                    
            if "city_distribution" in self.results["data_distribution"]:
                print("  Top Cities:")
                for city in self.results["data_distribution"]["city_distribution"][:5]:
                    print(f"    - {city['city']}: {city['percentage']}%")

if __name__ == "__main__":
    print("="*60)
    print("BIGQUERY PERFORMANCE PROFILER")
    print("="*60)
    
    profiler = BigQueryProfiler()
    profiler.run_full_profile()