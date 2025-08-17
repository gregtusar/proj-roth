"""Geospatial helper functions for BigQuery voter data queries."""

from typing import Tuple, Optional, List


class GeospatialQueryBuilder:
    """Helper class for building geospatial SQL queries for voter data."""
    
    # Common NJ locations with lat/lng coordinates
    NJ_LOCATIONS = {
        'summit_train': (-74.3574, 40.7155),
        'westfield_downtown': (-74.3473, 40.6502),
        'morristown_green': (-74.4810, 40.7968),
        'new_brunswick_rutgers': (-74.4474, 40.5008),
        'princeton_university': (-74.6551, 40.3487),
        'newark_penn': (-74.1645, 40.7342),
        'hoboken_terminal': (-74.0279, 40.7350),
        'trenton_capitol': (-74.7699, 40.2206),
        'elizabeth_city_hall': (-74.2107, 40.6640),
        'union_kean': (-74.2296, 40.6806),
    }
    
    # Conversion constants
    METERS_PER_MILE = 1609.34
    METERS_PER_KM = 1000
    
    @staticmethod
    def point_from_coords(lng: float, lat: float) -> str:
        """Generate ST_GEOGPOINT SQL from coordinates."""
        return f"ST_GEOGPOINT({lng}, {lat})"
    
    @staticmethod
    def miles_to_meters(miles: float) -> float:
        """Convert miles to meters for ST_DISTANCE."""
        return miles * GeospatialQueryBuilder.METERS_PER_MILE
    
    @classmethod
    def find_voters_within_radius(cls, 
                                   center_lat: float, 
                                   center_lng: float, 
                                   radius_miles: float,
                                   filters: Optional[str] = None) -> str:
        """
        Generate SQL to find voters within a radius of a point.
        
        Args:
            center_lat: Latitude of center point
            center_lng: Longitude of center point  
            radius_miles: Search radius in miles
            filters: Additional WHERE conditions (e.g., "demo_party = 'DEMOCRAT'")
            
        Returns:
            SQL query string
        """
        radius_meters = cls.miles_to_meters(radius_miles)
        center_point = cls.point_from_coords(center_lng, center_lat)
        
        sql = f"""
        SELECT *,
               ROUND(ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), {center_point}) / {cls.METERS_PER_MILE}, 2) as miles_from_center
        FROM voter_data.voters
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        AND ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), {center_point}) < {radius_meters}
        """
        
        if filters:
            sql += f"\nAND {filters}"
        
        sql += "\nORDER BY miles_from_center"
        
        return sql.strip()
    
    @classmethod
    def count_by_distance_rings(cls,
                                center_lat: float,
                                center_lng: float,
                                ring_distances: List[float] = None,
                                county: Optional[str] = None) -> str:
        """
        Generate SQL to count voters in distance rings around a point.
        
        Args:
            center_lat: Latitude of center point
            center_lng: Longitude of center point
            ring_distances: List of distances in miles for rings (default: [0.5, 1, 2, 5])
            county: Optional county filter
            
        Returns:
            SQL query string
        """
        if ring_distances is None:
            ring_distances = [0.5, 1, 2, 5]
        
        center_point = cls.point_from_coords(center_lng, center_lat)
        
        # Build CASE statement for distance rings
        case_clauses = []
        prev_dist = 0
        for dist in ring_distances:
            meters = cls.miles_to_meters(dist)
            if prev_dist == 0:
                case_clauses.append(f"WHEN distance_meters < {meters} THEN '0-{dist} miles'")
            else:
                case_clauses.append(f"WHEN distance_meters < {meters} THEN '{prev_dist}-{dist} miles'")
            prev_dist = dist
        case_clauses.append(f"ELSE '{prev_dist}+ miles'")
        
        case_statement = "CASE\n    " + "\n    ".join(case_clauses) + "\n  END"
        
        county_filter = f"AND county_name = '{county}'" if county else ""
        
        sql = f"""
        SELECT 
          {case_statement} as distance_ring,
          COUNT(*) as total_voters,
          SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) as democrats,
          SUM(CASE WHEN demo_party = 'REPUBLICAN' THEN 1 ELSE 0 END) as republicans,
          SUM(CASE WHEN demo_party = 'UNAFFILIATED' THEN 1 ELSE 0 END) as unaffiliated,
          ROUND(100.0 * SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) / COUNT(*), 1) as democrat_pct
        FROM (
          SELECT demo_party,
                 ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), {center_point}) as distance_meters
          FROM voter_data.voters
          WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          {county_filter}
        )
        GROUP BY distance_ring
        ORDER BY 
          CASE distance_ring
            {chr(10).join(f"WHEN '{f'0-{ring_distances[0]} miles' if i == 0 else f'{ring_distances[i-1]}-{dist} miles'}' THEN {i+1}" for i, dist in enumerate(ring_distances))}
            ELSE {len(ring_distances) + 1}
          END
        """
        
        return sql.strip()
    
    @classmethod
    def find_nearest_high_turnout_dems(cls,
                                       center_lat: float,
                                       center_lng: float,
                                       limit: int = 100) -> str:
        """
        Find nearest high-turnout Democratic voters to a location.
        
        Args:
            center_lat: Latitude of center point
            center_lng: Longitude of center point
            limit: Maximum number of results
            
        Returns:
            SQL query string
        """
        center_point = cls.point_from_coords(center_lng, center_lat)
        
        sql = f"""
        SELECT 
          name_first,
          name_last,
          addr_residential_street_number,
          addr_residential_street_name,
          addr_residential_city,
          ROUND(ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), {center_point}) / {cls.METERS_PER_MILE}, 2) as miles_away,
          (CAST(participation_primary_2020 AS INT) + 
           CAST(participation_primary_2022 AS INT) + 
           CAST(participation_primary_2024 AS INT) +
           CAST(participation_general_2020 AS INT) + 
           CAST(participation_general_2022 AS INT) + 
           CAST(participation_general_2024 AS INT)) as elections_voted_recent
        FROM voter_data.voters
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        AND demo_party = 'DEMOCRAT'
        AND (participation_general_2020 = TRUE OR participation_general_2022 = TRUE OR participation_general_2024 = TRUE)
        ORDER BY ST_DISTANCE(ST_GEOGPOINT(longitude, latitude), {center_point})
        LIMIT {limit}
        """
        
        return sql.strip()
    
    @classmethod
    def analyze_street_walkability(cls,
                                   street_name: str,
                                   city: str) -> str:
        """
        Analyze a street for campaign walkability - voter density and party distribution.
        
        Args:
            street_name: Name of the street (will be uppercased)
            city: City name (will be uppercased)
            
        Returns:
            SQL query string
        """
        sql = f"""
        WITH street_stats AS (
          SELECT 
            addr_residential_street_name,
            addr_residential_city,
            COUNT(*) as total_voters,
            SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) as dems,
            MIN(latitude) as min_lat,
            MAX(latitude) as max_lat,
            MIN(longitude) as min_lng,
            MAX(longitude) as max_lng,
            AVG(latitude) as center_lat,
            AVG(longitude) as center_lng
          FROM voter_data.voters
          WHERE addr_residential_street_name = '{street_name.upper()}'
          AND addr_residential_city = '{city.upper()}'
          AND latitude IS NOT NULL
          GROUP BY addr_residential_street_name, addr_residential_city
        )
        SELECT 
          addr_residential_street_name as street,
          addr_residential_city as city,
          total_voters,
          dems as democrats,
          ROUND(100.0 * dems / total_voters, 1) as democrat_pct,
          ROUND(ST_DISTANCE(
            ST_GEOGPOINT(min_lng, min_lat),
            ST_GEOGPOINT(max_lng, max_lat)
          ) / {cls.METERS_PER_MILE}, 2) as street_length_miles,
          ROUND(total_voters / NULLIF(ST_DISTANCE(
            ST_GEOGPOINT(min_lng, min_lat),
            ST_GEOGPOINT(max_lng, max_lat)
          ) / {cls.METERS_PER_MILE}, 0), 0) as voters_per_mile,
          center_lat,
          center_lng
        FROM street_stats
        """
        
        return sql.strip()
    
    @classmethod
    def find_dense_dem_areas(cls, county: str, min_voters: int = 50) -> str:
        """
        Find areas with high Democratic voter density.
        
        Args:
            county: County name (will be uppercased)
            min_voters: Minimum voters to consider
            
        Returns:
            SQL query string
        """
        sql = f"""
        SELECT 
          addr_residential_city,
          addr_residential_street_name,
          COUNT(*) as total_voters,
          SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) as democrats,
          ROUND(100.0 * SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) / COUNT(*), 1) as democrat_pct,
          AVG(latitude) as center_lat,
          AVG(longitude) as center_lng,
          -- Calculate geographic spread
          ROUND(ST_DISTANCE(
            ST_GEOGPOINT(MIN(longitude), MIN(latitude)),
            ST_GEOGPOINT(MAX(longitude), MAX(latitude))
          ) / {cls.METERS_PER_MILE}, 2) as area_span_miles
        FROM voter_data.voters
        WHERE county_name = '{county.upper()}'
        AND latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY addr_residential_city, addr_residential_street_name
        HAVING COUNT(*) >= {min_voters}
        AND SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) / COUNT(*) > 0.5
        ORDER BY democrat_pct DESC, total_voters DESC
        LIMIT 25
        """
        
        return sql.strip()
    
    @classmethod
    def create_heat_map_data(cls, county: str, grid_size_miles: float = 0.5) -> str:
        """
        Create data for a voter heat map by dividing area into grid squares.
        
        Args:
            county: County name
            grid_size_miles: Size of each grid square in miles
            
        Returns:
            SQL query string
        """
        grid_degrees = grid_size_miles / 69  # Rough conversion for latitude
        
        sql = f"""
        SELECT 
          ROUND(latitude / {grid_degrees}) * {grid_degrees} as grid_lat,
          ROUND(longitude / {grid_degrees}) * {grid_degrees} as grid_lng,
          COUNT(*) as total_voters,
          SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) as democrats,
          SUM(CASE WHEN demo_party = 'REPUBLICAN' THEN 1 ELSE 0 END) as republicans,
          ROUND(100.0 * SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) / COUNT(*), 1) as democrat_pct,
          SUM(CASE WHEN participation_general_2024 = TRUE THEN 1 ELSE 0 END) as voted_2024
        FROM voter_data.voters
        WHERE county_name = '{county.upper()}'
        AND latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY grid_lat, grid_lng
        HAVING COUNT(*) > 10
        ORDER BY total_voters DESC
        """
        
        return sql.strip()


# Convenience functions for direct use
def voters_within_mile(lat: float, lng: float) -> str:
    """Quick function to find all voters within 1 mile of a point."""
    return GeospatialQueryBuilder.find_voters_within_radius(lat, lng, 1.0)


def campaign_headquarters_analysis(lat: float, lng: float) -> str:
    """Analyze voter distribution around a potential campaign HQ location."""
    return GeospatialQueryBuilder.count_by_distance_rings(lat, lng, [0.25, 0.5, 1, 2, 3])


def walkable_streets_nearby(lat: float, lng: float, max_distance_miles: float = 1.0) -> str:
    """Find high-density Democratic streets within walking distance."""
    sql = f"""
    WITH street_centers AS (
      SELECT 
        addr_residential_street_name,
        addr_residential_city,
        COUNT(*) as voter_count,
        SUM(CASE WHEN demo_party = 'DEMOCRAT' THEN 1 ELSE 0 END) as dem_count,
        AVG(latitude) as street_lat,
        AVG(longitude) as street_lng
      FROM voter_data.voters
      WHERE latitude IS NOT NULL
      GROUP BY addr_residential_street_name, addr_residential_city
      HAVING COUNT(*) >= 20
    )
    SELECT 
      addr_residential_street_name,
      addr_residential_city,
      voter_count,
      dem_count,
      ROUND(100.0 * dem_count / voter_count, 1) as dem_pct,
      ROUND(ST_DISTANCE(
        ST_GEOGPOINT(street_lng, street_lat),
        ST_GEOGPOINT({lng}, {lat})
      ) / {GeospatialQueryBuilder.METERS_PER_MILE}, 2) as miles_away
    FROM street_centers
    WHERE ST_DISTANCE(
      ST_GEOGPOINT(street_lng, street_lat),
      ST_GEOGPOINT({lng}, {lat})
    ) < {max_distance_miles * GeospatialQueryBuilder.METERS_PER_MILE}
    AND dem_count > voter_count * 0.4
    ORDER BY dem_pct DESC, miles_away
    LIMIT 20
    """
    return sql.strip()