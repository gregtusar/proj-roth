"""
Simple agent implementation without ADK dependency
"""
import json
from typing import Dict, Any
from bigquery_tool import BigQueryReadOnlyTool
from google_search_tool import GoogleSearchTool
from geocoding_tool import GeocodingTool

class NJVoterChatAgent:
    """Simplified agent for NJ voter data queries without ADK dependency"""
    
    def __init__(self):
        self.bq_tool = BigQueryReadOnlyTool()
        self.search_tool = GoogleSearchTool()
        self.geocoding_tool = GeocodingTool()
        
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Process a chat message and return a response
        """
        message_lower = message.lower()
        
        # Handle BigQuery queries
        if any(keyword in message_lower for keyword in ['select', 'from', 'where', 'count', 'voters', 'party']):
            try:
                # Extract SQL-like parts from the message
                if 'select' in message_lower:
                    # User provided SQL directly
                    sql = message
                else:
                    # Generate basic SQL from natural language
                    sql = self._generate_sql_from_text(message)
                
                result = self.bq_tool.run({'query': sql})
                
                if 'error' in result:
                    return {"output": f"Query error: {result['error']}"}
                
                return {
                    "output": self._format_query_results(result)
                }
            except Exception as e:
                return {"output": f"Error processing query: {str(e)}"}
        
        # Handle geocoding requests
        if any(keyword in message_lower for keyword in ['geocode', 'coordinates', 'lat', 'lng', 'location']):
            try:
                # Extract address from message
                address = message.replace('geocode', '').replace('coordinates for', '').strip()
                result = self.geocoding_tool.run({'address': address})
                return {"output": json.dumps(result, indent=2)}
            except Exception as e:
                return {"output": f"Geocoding error: {str(e)}"}
        
        # Handle search requests
        if any(keyword in message_lower for keyword in ['search', 'find', 'news', 'information about']):
            try:
                # Extract search query
                query = message.replace('search for', '').replace('find', '').replace('search', '').strip()
                result = self.search_tool.run({'query': f"NJ politics {query}"})
                return {"output": self._format_search_results(result)}
            except Exception as e:
                return {"output": f"Search error: {str(e)}"}
        
        # Default response for unhandled queries
        return {
            "output": f"I can help you with:\n" +
                     "1. Query voter data (e.g., 'How many Democrats are in Hoboken?')\n" +
                     "2. Geocode addresses (e.g., 'geocode 123 Main St, Newark, NJ')\n" +
                     "3. Search for NJ political information (e.g., 'search for NJ governor election')\n\n" +
                     f"Your message: '{message}'"
        }
    
    def _generate_sql_from_text(self, text: str) -> str:
        """Generate basic SQL from natural language"""
        text_lower = text.lower()
        
        # Basic patterns
        if 'count' in text_lower or 'how many' in text_lower:
            if 'democrat' in text_lower:
                city = self._extract_city(text)
                if city:
                    return f"SELECT COUNT(*) as count FROM `proj-roth.voter_data.voters` WHERE demo_party = 'DEM' AND addr_city = '{city.upper()}'"
                return "SELECT COUNT(*) as count FROM `proj-roth.voter_data.voters` WHERE demo_party = 'DEM'"
            
            if 'republican' in text_lower:
                city = self._extract_city(text)
                if city:
                    return f"SELECT COUNT(*) as count FROM `proj-roth.voter_data.voters` WHERE demo_party = 'REP' AND addr_city = '{city.upper()}'"
                return "SELECT COUNT(*) as count FROM `proj-roth.voter_data.voters` WHERE demo_party = 'REP'"
        
        # Default query
        return "SELECT COUNT(*) as total_voters FROM `proj-roth.voter_data.voters` LIMIT 10"
    
    def _extract_city(self, text: str) -> str:
        """Extract city name from text"""
        # Common NJ cities
        cities = ['hoboken', 'newark', 'jersey city', 'elizabeth', 'paterson', 'trenton', 
                 'clifton', 'camden', 'passaic', 'union city', 'summit', 'westfield']
        
        text_lower = text.lower()
        for city in cities:
            if city in text_lower:
                return city.upper().replace(' ', '_')
        
        # Try to extract after "in"
        if ' in ' in text_lower:
            parts = text_lower.split(' in ')
            if len(parts) > 1:
                potential_city = parts[1].strip().split()[0]
                return potential_city.upper()
        
        return ""
    
    def _format_query_results(self, result: Dict) -> str:
        """Format query results for display"""
        if 'data' in result:
            rows = result['data']
            if not rows:
                return "No results found."
            
            # Format as readable text
            if len(rows) == 1 and 'count' in rows[0]:
                return f"Result: {rows[0]['count']:,} voters"
            
            # Format table
            output = f"Found {len(rows)} results:\n\n"
            for i, row in enumerate(rows[:10], 1):  # Limit display to 10 rows
                output += f"{i}. {json.dumps(row, indent=2)}\n"
            
            if len(rows) > 10:
                output += f"\n... and {len(rows) - 10} more rows"
            
            return output
        
        return str(result)
    
    def _format_search_results(self, result: Dict) -> str:
        """Format search results for display"""
        if isinstance(result, dict) and 'results' in result:
            items = result['results']
            if not items:
                return "No search results found."
            
            output = f"Found {len(items)} results:\n\n"
            for i, item in enumerate(items[:5], 1):
                output += f"{i}. {item.get('title', 'No title')}\n"
                output += f"   {item.get('snippet', '')}\n"
                output += f"   Link: {item.get('link', '')}\n\n"
            
            return output
        
        return str(result)
