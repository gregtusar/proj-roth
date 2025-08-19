"""
Vector storage for RAG-based retrieval of Reddit content.
Uses ChromaDB for local vector storage with semantic search capabilities.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import hashlib

from ..models.reddit_data import RedditPost, RedditComment, ContentRelevance, PoliticalTopic

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for Reddit content with RAG capabilities."""
    
    def __init__(
        self,
        persist_directory: str = "data/chroma",
        collection_name: str = "westfield_politics",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
            embedding_model: Name of the sentence transformer model
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Set up embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_post(self, post: RedditPost):
        """
        Add a Reddit post to the vector store.
        
        Args:
            post: RedditPost object to add
        """
        # Create document text for embedding
        doc_text = self._create_post_document(post)
        
        # Create unique ID
        doc_id = f"post_{post.id}"
        
        # Prepare metadata
        metadata = {
            "type": "post",
            "post_id": post.id,
            "author": post.author,
            "subreddit": post.subreddit,
            "created_utc": post.created_utc.isoformat(),
            "score": post.score,
            "num_comments": post.num_comments,
            "relevance": post.relevance.value,
            "topics": ",".join([t.value for t in post.topics]),
            "locations": ",".join(post.locations_mentioned),
            "politicians": ",".join(post.politicians_mentioned),
            "issues": ",".join(post.issues_mentioned),
            "sentiment": post.sentiment_score or 0.0,
            "url": post.permalink
        }
        
        # Add to collection
        self.collection.upsert(
            ids=[doc_id],
            documents=[doc_text],
            metadatas=[metadata]
        )
        
        logger.debug(f"Added post {post.id} to vector store")
    
    def add_comment(self, comment: RedditComment, post_id: str):
        """
        Add a Reddit comment to the vector store.
        
        Args:
            comment: RedditComment object to add
            post_id: ID of the parent post
        """
        # Create document text
        doc_text = comment.body
        
        # Create unique ID
        doc_id = f"comment_{comment.id}"
        
        # Prepare metadata
        metadata = {
            "type": "comment",
            "comment_id": comment.id,
            "post_id": post_id,
            "author": comment.author,
            "created_utc": comment.created_utc.isoformat(),
            "score": comment.score,
            "relevance": comment.relevance.value,
            "topics": ",".join([t.value for t in comment.topics]),
            "sentiment": comment.sentiment_score or 0.0,
            "url": comment.permalink
        }
        
        # Add to collection
        self.collection.upsert(
            ids=[doc_id],
            documents=[doc_text],
            metadatas=[metadata]
        )
        
        logger.debug(f"Added comment {comment.id} to vector store")
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        relevance_threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for relevant content using semantic similarity.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Metadata filters (e.g., {"type": "post"})
            relevance_threshold: Minimum relevance score (0-1)
        
        Returns:
            List of (metadata, score) tuples
        """
        # Build where clause for filtering
        where = {}
        if filter_metadata:
            where.update(filter_metadata)
        
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where if where else None
        )
        
        # Process results
        output = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # Convert distance to similarity score (1 - distance for cosine)
                score = 1 - distance
                
                # Apply relevance threshold if specified
                if relevance_threshold is None or score >= relevance_threshold:
                    output.append((metadata, score))
        
        return output
    
    def search_by_topic(
        self,
        topic: PoliticalTopic,
        n_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for content by political topic.
        
        Args:
            topic: Political topic to search for
            n_results: Number of results
        
        Returns:
            List of metadata dictionaries
        """
        # Use topic description as query
        topic_queries = {
            PoliticalTopic.ELECTIONS: "elections voting candidates campaign",
            PoliticalTopic.TAXES: "taxes property tax income tax budget",
            PoliticalTopic.EDUCATION: "schools education teachers students",
            PoliticalTopic.INFRASTRUCTURE: "roads bridges infrastructure construction",
            PoliticalTopic.HOUSING: "housing affordability rent mortgage development",
            PoliticalTopic.ENVIRONMENT: "environment climate pollution sustainability",
            PoliticalTopic.CRIME_SAFETY: "crime safety police security",
            PoliticalTopic.HEALTHCARE: "healthcare insurance medical hospitals",
            PoliticalTopic.TRANSPORTATION: "transportation transit traffic commute",
            PoliticalTopic.ECONOMY: "economy jobs business employment",
            PoliticalTopic.SOCIAL_ISSUES: "social justice equality rights",
            PoliticalTopic.LOCAL_GOVERNMENT: "mayor council government administration",
            PoliticalTopic.STATE_POLITICS: "governor legislature state politics"
        }
        
        query = topic_queries.get(topic, topic.value)
        
        # Search with topic filter
        results = self.search(
            query=query,
            n_results=n_results,
            filter_metadata={"topics": {"$contains": topic.value}}
        )
        
        return [r[0] for r in results]
    
    def search_by_location(
        self,
        location: str,
        n_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for content mentioning a specific location.
        
        Args:
            location: Location name
            n_results: Number of results
        
        Returns:
            List of metadata dictionaries
        """
        # Search for location mentions
        results = self.search(
            query=location,
            n_results=n_results,
            filter_metadata={"locations": {"$contains": location}}
        )
        
        return [r[0] for r in results]
    
    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        include_metadata: bool = True
    ) -> str:
        """
        Get contextual information for a query to use with LLM.
        
        Args:
            query: User query
            max_tokens: Approximate max tokens for context
            include_metadata: Whether to include metadata in context
        
        Returns:
            Formatted context string
        """
        # Search for relevant content
        results = self.search(query, n_results=20)
        
        context_parts = []
        token_count = 0
        
        for metadata, score in results:
            # Estimate tokens (rough approximation)
            if metadata["type"] == "post":
                content = self._format_post_context(metadata, include_metadata)
            else:
                content = self._format_comment_context(metadata, include_metadata)
            
            estimated_tokens = len(content.split()) * 1.3
            
            if token_count + estimated_tokens > max_tokens:
                break
            
            context_parts.append(content)
            token_count += estimated_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def _create_post_document(self, post: RedditPost) -> str:
        """Create searchable document text from post."""
        parts = [
            f"Title: {post.title}",
            f"Content: {post.selftext}" if post.selftext else "",
            f"Subreddit: r/{post.subreddit}",
            f"Author: {post.author}",
            f"Score: {post.score}",
            f"Comments: {post.num_comments}"
        ]
        
        if post.locations_mentioned:
            parts.append(f"Locations: {', '.join(post.locations_mentioned)}")
        
        if post.issues_mentioned:
            parts.append(f"Issues: {', '.join(post.issues_mentioned)}")
        
        if post.politicians_mentioned:
            parts.append(f"Politicians: {', '.join(post.politicians_mentioned)}")
        
        if post.summary:
            parts.append(f"Summary: {post.summary}")
        
        return "\n".join(filter(None, parts))
    
    def _format_post_context(
        self,
        metadata: Dict[str, Any],
        include_metadata: bool
    ) -> str:
        """Format post metadata for context."""
        parts = []
        
        if include_metadata:
            parts.append(f"[Reddit Post - Score: {metadata['score']}, Comments: {metadata['num_comments']}]")
            parts.append(f"Author: u/{metadata['author']}")
            parts.append(f"Posted: {metadata['created_utc']}")
        
        # Get actual document content
        result = self.collection.get(ids=[f"post_{metadata['post_id']}"])
        if result["documents"]:
            parts.append(result["documents"][0])
        
        if include_metadata and metadata.get("url"):
            parts.append(f"Link: {metadata['url']}")
        
        return "\n".join(parts)
    
    def _format_comment_context(
        self,
        metadata: Dict[str, Any],
        include_metadata: bool
    ) -> str:
        """Format comment metadata for context."""
        parts = []
        
        if include_metadata:
            parts.append(f"[Reddit Comment - Score: {metadata['score']}]")
            parts.append(f"Author: u/{metadata['author']}")
            parts.append(f"Posted: {metadata['created_utc']}")
        
        # Get actual document content
        result = self.collection.get(ids=[f"comment_{metadata['comment_id']}"])
        if result["documents"]:
            parts.append(result["documents"][0])
        
        return "\n".join(parts)
    
    def update_relevance_scores(self, batch_size: int = 100):
        """Update relevance scores for all documents based on engagement."""
        # Get all documents
        all_docs = self.collection.get()
        
        for i in range(0, len(all_docs["ids"]), batch_size):
            batch_ids = all_docs["ids"][i:i+batch_size]
            batch_metadatas = all_docs["metadatas"][i:i+batch_size]
            
            updated_metadatas = []
            for metadata in batch_metadatas:
                # Calculate relevance based on engagement
                if metadata["type"] == "post":
                    score = metadata.get("score", 0)
                    comments = metadata.get("num_comments", 0)
                    
                    # Simple engagement score
                    engagement = score + (comments * 2)
                    
                    if engagement > 100:
                        metadata["relevance"] = ContentRelevance.HIGH.value
                    elif engagement > 20:
                        metadata["relevance"] = ContentRelevance.MEDIUM.value
                    else:
                        metadata["relevance"] = ContentRelevance.LOW.value
                
                updated_metadatas.append(metadata)
            
            # Update batch
            self.collection.update(
                ids=batch_ids,
                metadatas=updated_metadatas
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        count = self.collection.count()
        
        # Get sample to analyze
        sample = self.collection.get(limit=1000)
        
        stats = {
            "total_documents": count,
            "posts": 0,
            "comments": 0,
            "high_relevance": 0,
            "medium_relevance": 0,
            "low_relevance": 0,
            "topics": {}
        }
        
        for metadata in sample["metadatas"]:
            # Count types
            if metadata["type"] == "post":
                stats["posts"] += 1
            else:
                stats["comments"] += 1
            
            # Count relevance
            relevance = metadata.get("relevance", "unknown")
            if relevance == ContentRelevance.HIGH.value:
                stats["high_relevance"] += 1
            elif relevance == ContentRelevance.MEDIUM.value:
                stats["medium_relevance"] += 1
            elif relevance == ContentRelevance.LOW.value:
                stats["low_relevance"] += 1
            
            # Count topics
            topics = metadata.get("topics", "").split(",")
            for topic in topics:
                if topic:
                    stats["topics"][topic] = stats["topics"].get(topic, 0) + 1
        
        return stats