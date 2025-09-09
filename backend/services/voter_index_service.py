"""Voter name indexing service with Trie-based search and Redis caching."""
import json
import logging
import pickle
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from google.cloud import bigquery

from core.config import get_settings

logger = logging.getLogger(__name__)


class TrieNode:
    """Node in the Trie data structure for prefix search."""
    
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word = False
        self.voter_refs: Set[str] = set()  # Store master_ids at this node


class VoterTrie:
    """Trie data structure for efficient prefix-based name search."""
    
    def __init__(self):
        self.root = TrieNode()
        self.voter_data: Dict[str, Dict] = {}  # master_id -> voter info
        
    def insert(self, word: str, master_id: str, voter_info: Dict):
        """Insert a word into the trie with associated voter data."""
        if not word:
            return
            
        word = word.upper().strip()
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            # Add voter reference at each prefix for progressive search
            node.voter_refs.add(master_id)
        
        node.is_end_of_word = True
        self.voter_data[master_id] = voter_info
    
    def search_prefix(self, prefix: str, limit: int = 20) -> List[Dict]:
        """Search for all voters whose names start with the given prefix."""
        if not prefix:
            return []
            
        prefix = prefix.upper().strip()
        node = self.root
        
        # Navigate to the prefix node
        for char in prefix:
            if char not in node.children:
                return []  # Prefix not found
            node = node.children[char]
        
        # Get all voter IDs under this prefix
        # Convert set to list first, then slice
        all_voter_ids = list(node.voter_refs)
        voter_ids = all_voter_ids[:limit * 3] if all_voter_ids else []  # Get extra to account for duplicates
        
        # Return unique voter data, sorted by name
        seen = set()
        results = []
        for voter_id in voter_ids:
            if voter_id not in seen and voter_id in self.voter_data:
                seen.add(voter_id)
                results.append(self.voter_data[voter_id])
                if len(results) >= limit:
                    break
        
        # Sort by last name, then first name
        results.sort(key=lambda x: (x.get('name_last', ''), x.get('name_first', '')))
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """Get statistics about the trie."""
        def count_nodes(node):
            count = 1
            for child in node.children.values():
                count += count_nodes(child)
            return count
        
        return {
            'total_voters': len(self.voter_data),
            'total_nodes': count_nodes(self.root),
            'memory_size_bytes': len(pickle.dumps(self))
        }


class VoterIndexService:
    """Service for managing voter name index with Redis caching."""
    
    REDIS_KEY_PREFIX = "voter_index"
    REDIS_TTL_HOURS = 24
    BATCH_SIZE = 10000
    
    # Class variable to hold the singleton instance
    _instance: Optional['VoterIndexService'] = None
    _initialized = False
    
    def __new__(cls):
        # Singleton pattern - return the same instance
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not VoterIndexService._initialized:
            self.settings = get_settings()
            self.redis_client: Optional[redis.Redis] = None
            self.trie: Optional[VoterTrie] = None
            self.last_update: Optional[datetime] = None
            self._init_lock = asyncio.Lock()
            VoterIndexService._initialized = True
        
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    decode_responses=False,  # We'll use pickle for complex objects
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                self.redis_client = None
        return self.redis_client
    
    async def initialize(self, force_rebuild: bool = False) -> bool:
        """Initialize the voter index, loading from cache or building if needed."""
        async with self._init_lock:
            try:
                if not force_rebuild:
                    # Try to load from cache first
                    loaded = await self._load_from_cache()
                    if loaded:
                        logger.info("Voter index loaded from cache")
                        return True
                
                # Build index from BigQuery
                logger.info("Building voter index from BigQuery...")
                await self._build_index()
                
                # Save to cache
                await self._save_to_cache()
                
                logger.info("Voter index initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize voter index: {e}")
                # Fallback to empty trie
                self.trie = VoterTrie()
                return False
    
    async def _load_from_cache(self) -> bool:
        """Load the trie from Redis cache."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return False
            
            # Check if index exists and is recent
            trie_data = await redis_client.get(f"{self.REDIS_KEY_PREFIX}:trie")
            metadata = await redis_client.get(f"{self.REDIS_KEY_PREFIX}:metadata")
            
            if not trie_data or not metadata:
                return False
            
            # Check age of index
            meta = json.loads(metadata)
            last_update = datetime.fromisoformat(meta['last_update'])
            if datetime.utcnow() - last_update > timedelta(hours=self.REDIS_TTL_HOURS):
                logger.info("Cache expired, will rebuild")
                return False
            
            # Load the trie
            self.trie = pickle.loads(trie_data)
            self.last_update = last_update
            
            logger.info(f"Loaded voter index from cache: {meta['stats']}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
            return False
    
    async def _save_to_cache(self) -> bool:
        """Save the trie to Redis cache."""
        try:
            if not self.trie:
                return False
                
            redis_client = await self._get_redis()
            if not redis_client:
                logger.warning("Redis not available, skipping cache save")
                return False
            
            # Serialize the trie
            trie_data = pickle.dumps(self.trie)
            
            # Save metadata
            metadata = {
                'last_update': datetime.utcnow().isoformat(),
                'stats': self.trie.get_stats()
            }
            
            # Store in Redis with TTL
            pipe = redis_client.pipeline()
            pipe.set(
                f"{self.REDIS_KEY_PREFIX}:trie", 
                trie_data,
                ex=self.REDIS_TTL_HOURS * 3600
            )
            pipe.set(
                f"{self.REDIS_KEY_PREFIX}:metadata",
                json.dumps(metadata),
                ex=self.REDIS_TTL_HOURS * 3600
            )
            await pipe.execute()
            
            logger.info(f"Saved voter index to cache: {metadata['stats']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")
            return False
    
    async def _build_index(self):
        """Build the voter index from BigQuery."""
        try:
            client = bigquery.Client(project=self.settings.GOOGLE_CLOUD_PROJECT)
            self.trie = VoterTrie()
            
            # Query to get ALL voters (even those without names)
            query = f"""
            SELECT DISTINCT
                v.master_id,
                i.name_first,
                i.name_middle,
                i.name_last,
                a.city,
                a.state,
                a.zip_code,
                a.standardized_address,
                v.demo_age,
                v.demo_party,
                v.email,
                v.vendor_voter_id
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.voters` v
            LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.individuals` i
                ON v.master_id = i.master_id
            LEFT JOIN `{self.settings.GOOGLE_CLOUD_PROJECT}.voter_data.addresses` a
                ON v.address_id = a.address_id
            """
            
            # Execute query
            logger.info("Querying BigQuery for voter names...")
            query_job = client.query(query)
            
            # Process results in batches
            total_processed = 0
            batch = []
            
            for row in query_job:
                voter_info = {
                    'master_id': row.master_id,
                    'name_first': row.name_first or '',
                    'name_middle': row.name_middle or '',
                    'name_last': row.name_last or '',
                    'city': row.city or '',
                    'state': row.state or '',
                    'zip': row.zip_code or '',
                    'address': row.standardized_address or '',
                    'age': row.demo_age,
                    'party': row.demo_party or '',
                    'email': row.email or ''
                }
                
                # Insert into trie - index by last name, first name, and full name
                if row.name_last:
                    self.trie.insert(row.name_last, row.master_id, voter_info)
                
                if row.name_first:
                    self.trie.insert(row.name_first, row.master_id, voter_info)
                
                # Also index by "last, first" format
                if row.name_last and row.name_first:
                    full_name = f"{row.name_last}, {row.name_first}"
                    self.trie.insert(full_name, row.master_id, voter_info)
                
                total_processed += 1
                if total_processed % 10000 == 0:
                    logger.info(f"Processed {total_processed} voters...")
            
            self.last_update = datetime.utcnow()
            logger.info(f"Built index with {total_processed} voters")
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Dict]:
        """
        Search for voters using the indexed trie.
        Supports progressive/typeahead search.
        """
        # Ensure index is initialized
        if not self.trie:
            await self.initialize()
        
        if not self.trie:
            # Fallback to empty results if initialization failed
            logger.warning("Trie not initialized, returning empty results")
            return []
        
        # Parse query - handle "last, first" format
        query = query.strip()
        
        # Search using the trie
        results = self.trie.search_prefix(query, limit)
        
        # Format results for API response
        formatted_results = []
        for voter in results:
            address = f"{voter.get('address', '')}, {voter.get('city', '')}, {voter.get('state', '')} {voter.get('zip', '')}"
            formatted_results.append({
                "master_id": voter.get("master_id"),
                "name": f"{voter.get('name_last', '')}, {voter.get('name_first', '')} {voter.get('name_middle', '')}".strip(),
                "address": address.strip(', '),
                "age": voter.get("age"),
                "party": voter.get("party"),
                "email": voter.get("email")
            })
        
        return formatted_results
    
    async def get_stats(self) -> Dict:
        """Get statistics about the index."""
        if not self.trie:
            return {"status": "not_initialized"}
        
        stats = self.trie.get_stats()
        stats['last_update'] = self.last_update.isoformat() if self.last_update else None
        stats['cache_ttl_hours'] = self.REDIS_TTL_HOURS
        
        return stats
    
    async def rebuild_index(self) -> Dict:
        """Force rebuild the index from BigQuery."""
        logger.info("Force rebuilding voter index...")
        success = await self.initialize(force_rebuild=True)
        
        if success:
            stats = await self.get_stats()
            return {
                "status": "success",
                "message": "Index rebuilt successfully",
                "stats": stats
            }
        else:
            return {
                "status": "error",
                "message": "Failed to rebuild index"
            }
    
    async def close(self):
        """Clean up resources."""
        if self.redis_client:
            await self.redis_client.close()