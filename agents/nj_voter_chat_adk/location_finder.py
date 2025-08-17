"""Location finder utilities for resolving place names to coordinates."""

from typing import Tuple, Optional, Dict, List
import re


class LocationFinder:
    """Helper class to find coordinates for location descriptions."""
    
    # Known landmarks and their coordinates
    NJ_LANDMARKS = {
        # Train stations
        'summit train': (-74.3574, 40.7155),
        'summit station': (-74.3574, 40.7155),
        'westfield train': (-74.3473, 40.6502),
        'westfield station': (-74.3473, 40.6502),
        'morristown train': (-74.4810, 40.7968),
        'morristown station': (-74.4810, 40.7968),
        'newark penn': (-74.1645, 40.7342),
        'newark penn station': (-74.1645, 40.7342),
        'hoboken terminal': (-74.0279, 40.7350),
        'new brunswick train': (-74.4474, 40.5008),
        
        # Universities/Colleges
        'rutgers': (-74.4474, 40.5008),
        'princeton': (-74.6551, 40.3487),
        'princeton university': (-74.6551, 40.3487),
        'kean university': (-74.2296, 40.6806),
        'kean': (-74.2296, 40.6806),
        'montclair state': (-74.1985, 40.8623),
        'seton hall': (-74.2469, 40.7420),
        
        # Government buildings
        'trenton capitol': (-74.7699, 40.2206),
        'trenton state house': (-74.7699, 40.2206),
        'elizabeth city hall': (-74.2107, 40.6640),
        'union county courthouse': (-74.3090, 40.6976),
        
        # Shopping/Downtown areas
        'westfield downtown': (-74.3473, 40.6502),
        'summit downtown': (-74.3574, 40.7155),
        'morristown green': (-74.4810, 40.7968),
        'short hills mall': (-74.3232, 40.7405),
        'menlo park mall': (-74.3345, 40.5484),
        'livingston mall': (-74.3154, 40.7956),
        
        # Parks
        'watchung reservation': (-74.3857, 40.6781),
        'nomahegan park': (-74.3272, 40.6564),
        'echo lake park': (-74.3330, 40.6819),
        'warinanco park': (-74.2938, 40.6719),
        
        # Hospitals
        'overlook hospital': (-74.3659, 40.7183),
        'overlook medical': (-74.3659, 40.7183),
        'morristown medical': (-74.4656, 40.8036),
        'saint barnabas': (-74.3228, 40.7528),
        'rwj university hospital': (-74.4403, 40.5067),
        'university hospital newark': (-74.1911, 40.7423),
    }
    
    # City center coordinates (approximate downtown areas)
    NJ_CITY_CENTERS = {
        'summit': (-74.3574, 40.7155),
        'westfield': (-74.3473, 40.6502),
        'cranford': (-74.2996, 40.6584),
        'elizabeth': (-74.2107, 40.6640),
        'union': (-74.2633, 40.6976),
        'springfield': (-74.3201, 40.7048),
        'millburn': (-74.3190, 40.7259),
        'short hills': (-74.3232, 40.7405),
        'new providence': (-74.4016, 40.6984),
        'berkeley heights': (-74.4227, 40.6806),
        'scotch plains': (-74.3894, 40.6547),
        'fanwood': (-74.3835, 40.6406),
        'plainfield': (-74.4074, 40.6338),
        'linden': (-74.2446, 40.6298),
        'rahway': (-74.2776, 40.6081),
        'clark': (-74.3118, 40.6223),
        'garwood': (-74.3230, 40.6515),
        'kenilworth': (-74.2904, 40.6767),
        'roselle': (-74.2585, 40.6523),
        'roselle park': (-74.2644, 40.6645),
        'mountainside': (-74.3579, 40.6725),
        'livingston': (-74.3154, 40.7959),
        'millburn': (-74.3013, 40.7345),
        'maplewood': (-74.2733, 40.7312),
        'south orange': (-74.2612, 40.7489),
        'morristown': (-74.4810, 40.7968),
        'madison': (-74.4170, 40.7598),
        'chatham': (-74.3839, 40.7409),
        'florham park': (-74.3882, 40.7879),
        'newark': (-74.1724, 40.7357),
        'jersey city': (-74.0431, 40.7178),
        'hoboken': (-74.0320, 40.7439),
        'trenton': (-74.7643, 40.2171),
        'princeton': (-74.6551, 40.3487),
        'new brunswick': (-74.4474, 40.4862),
    }
    
    @classmethod
    def find_coordinates(cls, location_text: str) -> Optional[Tuple[float, float]]:
        """
        Try to find coordinates for a location description.
        
        Args:
            location_text: Natural language location description
            
        Returns:
            Tuple of (longitude, latitude) or None if not found
        """
        location_lower = location_text.lower().strip()
        
        # Check landmarks first (more specific)
        for landmark, coords in cls.NJ_LANDMARKS.items():
            if landmark in location_lower:
                return coords
        
        # Check city centers
        for city, coords in cls.NJ_CITY_CENTERS.items():
            if city in location_lower:
                return coords
        
        return None
    
    @classmethod
    def generate_coordinate_query(cls, location_text: str) -> str:
        """
        Generate SQL to find coordinates for a location.
        
        Args:
            location_text: Natural language location description
            
        Returns:
            SQL query to find coordinates
        """
        # Try to find known coordinates first
        coords = cls.find_coordinates(location_text)
        if coords:
            return f"-- Using known coordinates for {location_text}\n-- Longitude: {coords[0]}, Latitude: {coords[1]}"
        
        # Parse for city name
        location_lower = location_text.lower()
        
        # Common patterns
        city_patterns = [
            r'in (\w+)',
            r'near (\w+)',
            r'around (\w+)',
            r'(\w+) area',
            r'downtown (\w+)',
            r'(\w+) downtown',
        ]
        
        city = None
        for pattern in city_patterns:
            match = re.search(pattern, location_lower)
            if match:
                potential_city = match.group(1).upper()
                # Check if it's a known city
                if potential_city.lower() in cls.NJ_CITY_CENTERS:
                    city = potential_city
                    break
        
        if city:
            return f"""-- Find center coordinates for {city}
WITH city_center AS (
  SELECT 
    AVG(latitude) as lat,
    AVG(longitude) as lng,
    COUNT(*) as voter_count
  FROM voter_data.voters
  WHERE addr_residential_city = '{city}'
  AND latitude IS NOT NULL
)
SELECT lat, lng FROM city_center"""
        
        # Parse for street and city
        street_match = re.search(r'(\w+)\s+(street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd)', location_lower)
        if street_match:
            street = street_match.group(1).upper()
            return f"""-- Find coordinates for {street} street
WITH street_center AS (
  SELECT 
    addr_residential_city,
    AVG(latitude) as lat,
    AVG(longitude) as lng,
    COUNT(*) as voter_count
  FROM voter_data.voters
  WHERE addr_residential_street_name = '{street}'
  AND latitude IS NOT NULL
  GROUP BY addr_residential_city
  ORDER BY voter_count DESC
  LIMIT 1
)
SELECT lat, lng, addr_residential_city FROM street_center"""
        
        # Default: suggest using web search
        return f"""-- Could not parse location: {location_text}
-- Option 1: Use google_search("{location_text} coordinates New Jersey")
-- Option 2: Find city center - replace CITYNAME:
SELECT AVG(latitude) as lat, AVG(longitude) as lng
FROM voter_data.voters
WHERE addr_residential_city = 'CITYNAME'
AND latitude IS NOT NULL"""
    
    @classmethod
    def create_location_based_query(cls, location_text: str, radius_miles: float = 1.0, filters: str = "") -> str:
        """
        Create a complete query for finding voters near a location.
        
        Args:
            location_text: Natural language location description
            radius_miles: Search radius in miles
            filters: Additional SQL filters
            
        Returns:
            Complete SQL query
        """
        coords = cls.find_coordinates(location_text)
        
        if coords:
            # We have coordinates, generate direct query
            lng, lat = coords
            radius_meters = radius_miles * 1609.34
            
            query = f"""-- Finding voters within {radius_miles} miles of {location_text}
-- Using coordinates: {lng}, {lat}
SELECT *,
       ROUND(ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), 
                        ST_GEOGPOINT({lng}, {lat})) / 1609.34, 2) as miles_away
FROM voter_data.voters
WHERE latitude IS NOT NULL
AND ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), 
               ST_GEOGPOINT({lng}, {lat})) < {radius_meters}"""
            
            if filters:
                query += f"\nAND {filters}"
            
            query += "\nORDER BY miles_away\nLIMIT 1000"
            
            return query
        
        else:
            # Need to find coordinates first
            return f"""-- Location not recognized: {location_text}
-- First, find coordinates for this location:

{cls.generate_coordinate_query(location_text)}

-- Then use those coordinates in a radius search:
-- (Replace LAT and LNG with the coordinates from above)
SELECT *,
       ROUND(ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), 
                        ST_GEOGPOINT(LNG, LAT)) / 1609.34, 2) as miles_away
FROM voter_data.voters
WHERE latitude IS NOT NULL
AND ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), 
               ST_GEOGPOINT(LNG, LAT)) < {radius_miles * 1609.34}
{f'AND {filters}' if filters else ''}
ORDER BY miles_away
LIMIT 1000"""
    
    @classmethod
    def suggest_location_methods(cls, location_text: str) -> List[str]:
        """
        Suggest different methods to find coordinates for a location.
        
        Args:
            location_text: Natural language location description
            
        Returns:
            List of suggested SQL queries or methods
        """
        suggestions = []
        
        # Check if we have it in landmarks
        if cls.find_coordinates(location_text):
            coords = cls.find_coordinates(location_text)
            suggestions.append(f"Known location: {coords[0]}, {coords[1]}")
        
        # Suggest city center
        for city in cls.NJ_CITY_CENTERS.keys():
            if city in location_text.lower():
                suggestions.append(f"""City center: 
SELECT AVG(latitude), AVG(longitude) 
FROM voter_data.voters 
WHERE addr_residential_city = '{city.upper()}'""")
                break
        
        # Suggest web search
        suggestions.append(f'Web search: google_search("{location_text} coordinates latitude longitude")')
        
        # Suggest nearby address
        suggestions.append("""Find from specific address:
SELECT latitude, longitude 
FROM voter_data.voters 
WHERE addr_residential_street_number = '123'
AND addr_residential_street_name = 'MAIN'
AND addr_residential_city = 'SUMMIT'
LIMIT 1""")
        
        return suggestions


# Helper function for common use cases
def find_location_coords(location: str) -> Optional[Tuple[float, float]]:
    """Quick function to get coordinates for a location."""
    return LocationFinder.find_coordinates(location)


def voters_near_location(location: str, radius_miles: float = 1.0, party: str = None) -> str:
    """Generate query to find voters near a named location."""
    filters = f"demo_party = '{party}'" if party else ""
    return LocationFinder.create_location_based_query(location, radius_miles, filters)