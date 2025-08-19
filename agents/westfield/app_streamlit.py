"""
Streamlit interface for Westfield Agent using ADK
"""

import os
import sys
from pathlib import Path
import streamlit as st
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.westfield.agent import chat_with_agent
from agents.westfield.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Westfield Agent - NJ Politics",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None


def main():
    """Main Streamlit interface."""
    
    # Header
    st.title("🏛️ Westfield Agent")
    st.subheader("NJ Local Politics Intelligence from Social Media")
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.info(
            "This agent monitors Reddit (r/newjersey) for discussions about "
            "local politics, with a focus on NJ Congressional District 07.\n\n"
            "**Data Sources:**\n"
            "- Reddit posts and comments\n"
            "- Vector database with semantic search\n"
            "- Real-time updates\n\n"
            "**Topics Tracked:**\n"
            "- Elections & candidates\n"
            "- Property taxes\n"
            "- School boards\n"
            "- Infrastructure\n"
            "- Public safety\n"
            "- Transportation"
        )
        
        # Example queries
        st.header("Example Queries")
        example_queries = [
            "What are the trending political topics?",
            "What are people saying about property taxes in Westfield?",
            "Show me discussions about the school board",
            "What issues are affecting Union County?",
            "Search for posts about NJ Transit problems",
            "What's the sentiment about Governor Murphy?"
        ]
        
        for query in example_queries:
            if st.button(query, key=query):
                st.session_state.messages.append({"role": "user", "content": query})
                with st.spinner("Searching Reddit data..."):
                    response = chat_with_agent(query, st.session_state.session_id)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        # Actions
        st.header("Actions")
        
        if st.button("🔄 Update Database"):
            with st.spinner("Downloading new posts..."):
                response = chat_with_agent("Download new posts from Reddit", st.session_state.session_id)
                st.success("Database updated!")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        if st.button("📊 Show Trending"):
            with st.spinner("Analyzing trends..."):
                response = chat_with_agent("What are the trending political topics?", st.session_state.session_id)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about NJ local politics..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Reddit data..."):
                    try:
                        response = chat_with_agent(prompt, st.session_state.session_id)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        logger.error(f"Chat error: {e}")
    
    with col2:
        # Quick stats
        st.header("Quick Stats")
        
        # Try to get stats from vector store
        try:
            from agents.westfield.storage.vector_store import VectorStore
            store = VectorStore()
            stats = store.get_statistics()
            
            st.metric("Total Documents", f"{stats['total_documents']:,}")
            st.metric("Posts", f"{stats['posts']:,}")
            st.metric("Comments", f"{stats['comments']:,}")
            
            # Relevance breakdown
            st.subheader("Content Relevance")
            if stats['total_documents'] > 0:
                high_pct = (stats['high_relevance'] / len(stats)) * 100
                med_pct = (stats['medium_relevance'] / len(stats)) * 100
                low_pct = (stats['low_relevance'] / len(stats)) * 100
                
                st.progress(high_pct / 100, text=f"High: {high_pct:.1f}%")
                st.progress(med_pct / 100, text=f"Medium: {med_pct:.1f}%")
                st.progress(low_pct / 100, text=f"Low: {low_pct:.1f}%")
            
        except Exception as e:
            st.info("No data indexed yet. Use the CLI to download initial data.")
            logger.debug(f"Stats error: {e}")
        
        # Last update time
        st.subheader("Last Update")
        st.text(datetime.now().strftime("%Y-%m-%d %H:%M"))


if __name__ == "__main__":
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        st.error(f"Configuration error: {e}")
        st.error("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        st.stop()
    
    main()