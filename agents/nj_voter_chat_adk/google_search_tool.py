from typing import Any, Dict, List, Optional
import time
import hashlib
import json
import os
from datetime import datetime, timedelta
import requests
from urllib.parse import quote_plus
from debug_config import debug_print, error_print
from secret_manager import load_secret


class GoogleSearchTool:
    """Google Custom Search API tool with caching and rate limiting."""
    
    name = "google_search"
    description = "Search Google for current information about NJ politics, elections, and voter-related topics."
    
    def _read_secret(self, secret_name: str) -> Optional[str]:
        """Read a secret from a file.
        
        Args:
            secret_name: Name of the secret file (e.g., 'api-key', 'search-engine-id')
            
        Returns:
            The secret value or None if not found
        """
        secret_paths = [
            f"/run/secrets/{secret_name}",  # Docker/Kubernetes style
            f"/etc/secrets/{secret_name}",  # System secrets
            os.path.expanduser(f"~/.secrets/{secret_name}"),  # User home secrets
            os.path.join(os.path.dirname(__file__), "secrets", secret_name),  # Local secrets folder
        ]
        
        for path in secret_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        value = f.read().strip()
                        if value:
                            debug_print(f"[DEBUG] Loaded {secret_name} from {path}")
                            return value
                except Exception as e:
                    print(f"[WARNING] Could not read secret from {path}: {e}")
        
        return None
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """Initialize the Google Search tool.
        
        Args:
            api_key: Google Custom Search API key
            search_engine_id: Custom Search Engine ID
        """
        # Try multiple sources for credentials:
        # 1. Provided arguments
        # 2. Google Secret Manager (with correct secret names)
        # 3. Local secret files
        # 4. Environment variables
        
        self.api_key = (
            api_key or 
            load_secret("google-search-api-key", "GOOGLE_SEARCH_API_KEY") or
            load_secret("api-key", "GOOGLE_SEARCH_API_KEY") or  # This is the actual secret name in your project
            self._read_secret("api-key") or 
            os.getenv("GOOGLE_SEARCH_API_KEY")
        )
        
        self.search_engine_id = (
            search_engine_id or 
            load_secret("google-search-cx", "GOOGLE_SEARCH_ENGINE_ID") or
            load_secret("search-engine-id", "GOOGLE_SEARCH_ENGINE_ID") or  # This is the actual secret name
            self._read_secret("search-engine-id") or 
            os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        )
        
        if not self.api_key or not self.search_engine_id:
            print("[WARNING] Google Search API credentials not configured. Search functionality will be limited.")
        
        # Simple in-memory cache with TTL
        self._cache = {}  # {cache_key: {"results": [...], "timestamp": datetime}}
        self._cache_ttl = int(os.getenv("SEARCH_CACHE_TTL", "3600"))  # 1 hour default
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute window
        self._rate_limit_max = int(os.getenv("SEARCH_RATE_LIMIT", "10"))  # 10 requests per minute
        self._request_times = []
        
        # API endpoint
        self.api_url = "https://www.googleapis.com/customsearch/v1"
    
    def _get_cache_key(self, query: str, num_results: int) -> str:
        """Generate a cache key for the query."""
        key_str = f"{query}:{num_results}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if we have a valid cached result."""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now() - cached["timestamp"]).total_seconds()
            if age < self._cache_ttl:
                debug_print(f"[DEBUG] Cache hit for search query (age: {age:.0f}s)")
                return cached["results"]
        return None
    
    def _update_cache(self, cache_key: str, results: Dict[str, Any]):
        """Update the cache with new results."""
        self._cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now()
        }
        # Clean old cache entries
        self._clean_cache()
    
    def _clean_cache(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = []
        for key, value in self._cache.items():
            age = (now - value["timestamp"]).total_seconds()
            if age > self._cache_ttl:
                expired_keys.append(key)
        for key in expired_keys:
            del self._cache[key]
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        # Remove requests outside the window
        self._request_times = [t for t in self._request_times if now - t < self._rate_limit_window]
        
        if len(self._request_times) >= self._rate_limit_max:
            print(f"[WARNING] Rate limit reached: {len(self._request_times)} requests in last minute")
            return False
        
        self._request_times.append(now)
        return True
    
    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search Google for information.
        
        Args:
            query: The search query
            num_results: Number of results to return (max 10)
        
        Returns:
            Dictionary containing search results or error information
        """
        try:
            # Validate inputs
            if not query or not query.strip():
                return {"error": "Search query cannot be empty"}
            
            num_results = min(max(1, num_results), 10)  # Clamp between 1 and 10
            
            # Check cache first
            cache_key = self._get_cache_key(query, num_results)
            cached_results = self._check_cache(cache_key)
            if cached_results:
                return cached_results
            
            # Check if API is configured
            if not self.api_key or not self.search_engine_id:
                return {
                    "error": "Google Search API not configured. Please set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables.",
                    "query": query,
                    "results": []
                }
            
            # Check rate limit
            if not self._check_rate_limit():
                return {
                    "error": "Rate limit exceeded. Please wait before making more search requests.",
                    "query": query,
                    "results": []
                }
            
            # Make API request
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": num_results,
                "safe": "active",  # Safe search
                # Optional: Add site restrictions for NJ-specific sources
                # "siteSearch": "nj.gov OR nj.com OR northjersey.com",
                # "siteSearchFilter": "i"  # include these sites
            }
            
            debug_print(f"[DEBUG] Searching Google for: {query[:100]}...")
            response = requests.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 429:
                return {
                    "error": "Google API quota exceeded. Daily limit reached.",
                    "query": query,
                    "results": []
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            results = []
            items = data.get("items", [])
            
            for item in items[:num_results]:
                result = {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "display_link": item.get("displayLink", "")
                }
                # Add metadata if available
                if "pagemap" in item and "metatags" in item["pagemap"]:
                    metatags = item["pagemap"]["metatags"][0] if item["pagemap"]["metatags"] else {}
                    result["published_date"] = metatags.get("article:published_time", "")
                
                results.append(result)
            
            output = {
                "query": query,
                "total_results": int(data.get("searchInformation", {}).get("totalResults", 0)),
                "search_time": float(data.get("searchInformation", {}).get("searchTime", 0)),
                "results": results,
                "result_count": len(results)
            }
            
            # Cache the results
            self._update_cache(cache_key, output)
            
            debug_print(f"[DEBUG] Search returned {len(results)} results")
            return output
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Search request failed: {str(e)}"
            error_print(f"[ERROR] {error_msg}")
            return {
                "error": error_msg,
                "query": query,
                "results": []
            }
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            error_print(f"[ERROR] {error_msg}")
            return {
                "error": error_msg,
                "query": query,
                "results": []
            }
    
    def search_nj_specific(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search with focus on NJ-specific sources.
        
        This method adds NJ-specific context and site restrictions.
        """
        # Add NJ context if not already present
        if "nj" not in query.lower() and "new jersey" not in query.lower():
            query = f"{query} New Jersey"
        
        return self.search(query, num_results)
