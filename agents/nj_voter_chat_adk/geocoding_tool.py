from typing import Any, Dict, List, Optional
import os
import requests
from urllib.parse import quote_plus
import time
import hashlib
from datetime import datetime


class GeocodingTool:
    """Google Maps Geocoding API tool for converting addresses to coordinates."""
    
    name = "geocode_address"
    description = "Convert addresses to latitude/longitude coordinates using Google Maps. Useful for finding exact locations of addresses, businesses, or landmarks in New Jersey."
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Geocoding tool.
        
        Args:
            api_key: Google Maps API key
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        
        if not self.api_key:
            # Try to read from secrets file
            secret_paths = [
                f"/run/secrets/maps-api-key",
                os.path.join(os.path.dirname(__file__), "secrets", "maps-api-key"),
            ]
            for path in secret_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            self.api_key = f.read().strip()
                            if self.api_key:
                                break
                    except:
                        pass
        
        if not self.api_key:
            print("[WARNING] Google Maps API key not configured. Geocoding will be limited.")
        
        # Simple cache for geocoding results
        self._cache = {}  # {address_hash: {"lat": ..., "lng": ..., "formatted": ..., "timestamp": ...}}
        self._cache_ttl = 86400  # 24 hours
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 10 requests per second max
        
        # API endpoint
        self.api_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def _get_cache_key(self, address: str) -> str:
        """Generate a cache key for the address."""
        return hashlib.md5(address.lower().strip().encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if we have a valid cached result."""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now() - cached["timestamp"]).total_seconds()
            if age < self._cache_ttl:
                print(f"[DEBUG] Geocoding cache hit (age: {age:.0f}s)")
                return {
                    "latitude": cached["lat"],
                    "longitude": cached["lng"],
                    "formatted_address": cached["formatted"],
                    "from_cache": True
                }
        return None
    
    def _update_cache(self, cache_key: str, lat: float, lng: float, formatted: str):
        """Update the cache with new results."""
        self._cache[cache_key] = {
            "lat": lat,
            "lng": lng,
            "formatted": formatted,
            "timestamp": datetime.now()
        }
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()
    
    def geocode(self, address: str, bounds: Optional[str] = None) -> Dict[str, Any]:
        """Convert an address to coordinates.
        
        Args:
            address: The address to geocode (e.g., "123 Main St, Summit, NJ")
            bounds: Optional bounding box to prefer results within (e.g., "40.5,-75.0|41.0,-74.0" for NJ)
        
        Returns:
            Dictionary with latitude, longitude, and formatted address
        """
        try:
            # Validate input
            if not address or not address.strip():
                return {"error": "Address cannot be empty"}
            
            # Add "New Jersey" if not present and no state specified
            address_lower = address.lower()
            if "nj" not in address_lower and "new jersey" not in address_lower:
                # Check if any state is mentioned
                states = ["ny", "new york", "pa", "pennsylvania", "ct", "connecticut"]
                if not any(state in address_lower for state in states):
                    address = f"{address}, New Jersey"
            
            # Check cache
            cache_key = self._get_cache_key(address)
            cached_result = self._check_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Check if API is configured
            if not self.api_key:
                # Fallback to approximate coordinates based on city
                return self._fallback_geocoding(address)
            
            # Rate limiting
            self._rate_limit()
            
            # Prepare API request
            params = {
                "address": address,
                "key": self.api_key,
                "region": "us",  # Bias toward US results
            }
            
            # Add bounds for New Jersey if not specified
            if not bounds:
                # Approximate bounds for New Jersey
                params["bounds"] = "38.93,-75.56|41.36,-73.88"
            else:
                params["bounds"] = bounds
            
            print(f"[DEBUG] Geocoding address: {address}")
            response = requests.get(self.api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    
                    # Cache the result
                    self._update_cache(
                        cache_key,
                        location["lat"],
                        location["lng"],
                        result["formatted_address"]
                    )
                    
                    return {
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "formatted_address": result["formatted_address"],
                        "place_id": result.get("place_id"),
                        "types": result.get("types", []),
                        "from_cache": False
                    }
                elif data["status"] == "ZERO_RESULTS":
                    return {
                        "error": "No results found for this address",
                        "address": address
                    }
                elif data["status"] == "OVER_QUERY_LIMIT":
                    return {
                        "error": "API quota exceeded",
                        "address": address
                    }
                else:
                    return {
                        "error": f"Geocoding failed: {data.get('status', 'Unknown error')}",
                        "address": address
                    }
            else:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "address": address
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Network error: {str(e)}",
                "address": address
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "address": address
            }
    
    def _fallback_geocoding(self, address: str) -> Dict[str, Any]:
        """Fallback geocoding using known NJ city centers when API is not available."""
        # Known city centers in NJ (same as in location_finder.py)
        city_centers = {
            "summit": (40.7155, -74.3574),
            "westfield": (40.6590, -74.3473),
            "cranford": (40.6584, -74.2995),
            "berkeley heights": (40.6826, -74.4388),
            "new providence": (40.6984, -74.4013),
            "chatham": (40.7409, -74.3837),
            "madison": (40.7598, -74.4171),
            "florham park": (40.7878, -74.3883),
            "springfield": (40.7015, -74.3201),
            "millburn": (40.7259, -74.3243),
            "short hills": (40.7479, -74.3254),
            "livingston": (40.7959, -74.3149),
            "bernardsville": (40.7187, -74.5693),
            "basking ridge": (40.7062, -74.5493),
            "warren": (40.6337, -74.5102),
            "watchung": (40.6378, -74.4509),
            "plainfield": (40.6337, -74.4074),
            "scotch plains": (40.6551, -74.3899),
            "fanwood": (40.6408, -74.3836),
            "mountainside": (40.6723, -74.3571),
            "garwood": (40.6515, -74.3227),
            "clark": (40.6223, -74.3113),
            "rahway": (40.6082, -74.2776),
            "linden": (40.6220, -74.2446),
            "elizabeth": (40.6639, -74.2107),
            "union": (40.6976, -74.2632),
            "kenilworth": (40.6764, -74.2907),
            "roselle": (40.6523, -74.2596),
            "roselle park": (40.6645, -74.2643),
            "hillside": (40.7012, -74.2301),
            "newark": (40.7357, -74.1724),
            "morristown": (40.7968, -74.4810),
            "morris plains": (40.8348, -74.4807),
            "parsippany": (40.8578, -74.4259),
        }
        
        address_lower = address.lower()
        
        # Try to find a matching city
        for city, coords in city_centers.items():
            if city in address_lower:
                return {
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "formatted_address": f"{city.title()}, NJ (approximate)",
                    "approximate": True,
                    "note": "Google Maps API not configured. Using approximate city center."
                }
        
        # Default to NJ center if no city match
        return {
            "latitude": 40.0583,
            "longitude": -74.4057,
            "formatted_address": "New Jersey (center)",
            "approximate": True,
            "error": "Could not geocode specific address without API key. Using NJ center.",
            "address": address
        }
    
    def batch_geocode(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Geocode multiple addresses.
        
        Args:
            addresses: List of addresses to geocode
        
        Returns:
            List of geocoding results
        """
        results = []
        for address in addresses:
            results.append(self.geocode(address))
        return results
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Convert coordinates to an address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        
        Returns:
            Dictionary with formatted address and components
        """
        try:
            if not self.api_key:
                return {
                    "error": "Reverse geocoding requires Google Maps API key",
                    "latitude": latitude,
                    "longitude": longitude
                }
            
            # Rate limiting
            self._rate_limit()
            
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key
            }
            
            print(f"[DEBUG] Reverse geocoding: {latitude}, {longitude}")
            response = requests.get(self.api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    return {
                        "formatted_address": result["formatted_address"],
                        "place_id": result.get("place_id"),
                        "types": result.get("types", []),
                        "latitude": latitude,
                        "longitude": longitude
                    }
                else:
                    return {
                        "error": f"Reverse geocoding failed: {data.get('status', 'Unknown')}",
                        "latitude": latitude,
                        "longitude": longitude
                    }
            else:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "latitude": latitude,
                    "longitude": longitude
                }
                
        except Exception as e:
            return {
                "error": f"Reverse geocoding error: {str(e)}",
                "latitude": latitude,
                "longitude": longitude
            }