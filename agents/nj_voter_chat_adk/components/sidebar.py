"""
Custom sidebar component with ChatGPT-style navigation
"""
import streamlit as st
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

def init_session_state():
    """Initialize sidebar session state"""
    if 'sidebar_expanded' not in st.session_state:
        st.session_state.sidebar_expanded = True
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'projects' not in st.session_state:
        st.session_state.projects = {
            'Default Project': []
        }
    if 'current_project' not in st.session_state:
        st.session_state.current_project = 'Default Project'

def render_sidebar():
    """Render the custom sidebar with ChatGPT-style navigation"""
    init_session_state()
    
    # Custom CSS for sidebar consistent with Base design system
    st.markdown("""
    <style>
    /* Import Inter font to match Base design */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Hide Streamlit's default pages navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Sidebar styling - match main page background */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #F6F6F6;  /* --gray-50 from Base design */
        padding: 0;
        width: 280px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding: 0;
    }
    
    /* Ensure all text uses Inter font */
    [data-testid="stSidebar"] * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Remove old toggle button styling as it's now in main app */
    
    /* Navigation items */
    .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        color: #3B5D7C;  /* Wolf blue for text */
        text-decoration: none;
        transition: background 0.2s;
        cursor: pointer;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: 500;
        border-radius: 8px;
        margin: 4px 8px;
        width: calc(100% - 16px);
    }
    
    .nav-item:hover {
        background: #EEEEEE;
    }
    
    .nav-item.active {
        background: #E2E2E2;
    }
    
    .nav-item-icon {
        width: 20px;
        height: 20px;
        margin-right: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Section headers */
    .section-header {
        color: #757575;  /* --gray-500 */
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        padding: 12px 16px 8px 16px;
        margin-top: 16px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chat list items */
    .chat-item {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        color: #3B5D7C;  /* Wolf blue */
        text-decoration: none;
        transition: background 0.2s;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
        border-radius: 8px;
        margin: 2px 8px;
        width: calc(100% - 16px);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .chat-item:hover {
        background: #EEEEEE;
    }
    
    .chat-item.active {
        background: #E2E2E2;
        font-weight: 500;
    }
    
    /* New chat button */
    .new-chat-btn {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 12px 8px;
        background: #000000;  /* Black button like main page */
        border: none;
        border-radius: 8px;
        color: #FFFFFF;
        cursor: pointer;
        transition: all 0.2s;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: 500;
        width: calc(100% - 16px);
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .new-chat-btn:hover {
        background: #1F1F1F;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    /* Project tree */
    .project-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 16px;
        color: #3B5D7C;
        cursor: pointer;
        transition: background 0.2s;
        border-radius: 8px;
        margin: 2px 8px;
        width: calc(100% - 16px);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
    }
    
    .project-header:hover {
        background: #EEEEEE;
    }
    
    .project-content {
        padding-left: 24px;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: #757575;
    }
    
    /* Tools section */
    .tool-item {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        color: #3B5D7C;
        cursor: pointer;
        transition: background 0.2s;
        border-radius: 8px;
        margin: 2px 8px;
        width: calc(100% - 16px);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
    }
    
    .tool-item:hover {
        background: #EEEEEE;
    }
    
    .tool-item-icon {
        width: 20px;
        height: 20px;
        margin-right: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Divider */
    .sidebar-divider {
        height: 1px;
        background: #E2E2E2;  /* --gray-200 */
        margin: 16px 16px;
    }
    
    /* Empty state text */
    .empty-state {
        color: #757575;  /* --gray-500 */
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 400;
        padding: 8px 16px;
        font-style: italic;
    }
    
    /* Hide default Streamlit sidebar elements */
    .css-1d391kg > div > div > div > div:first-child {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # New Chat Button
        st.markdown("""
        <button class="new-chat-btn" onclick="window.location.reload()">
            <span>New chat</span>
        </button>
        """, unsafe_allow_html=True)
        
        # Projects Section
        render_projects_section()
        
        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Recent Chats Section
        render_chats_section()
        
        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Tools Section
        render_tools_section()

def render_projects_section():
    """Render the projects tree section"""
    st.markdown('<div class="section-header">Projects</div>', unsafe_allow_html=True)
    
    # Default project header with custom styling - using project-name class
    st.markdown("""
    <div class="project-header">
        <span class="project-name">Default Project</span>
        <span style="font-size: 12px; color: #757575;">▼</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Project content
    if st.session_state.projects.get('Default Project'):
        for chat in st.session_state.projects['Default Project']:
            st.markdown(f"""
            <div class="chat-item" onclick="window.location.reload()">
                {chat['title']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            No chats in this project
        </div>
        """, unsafe_allow_html=True)
    
    # Add new project button with consistent styling
    st.markdown("""
    <div class="tool-item" style="margin-top: 8px;">
        <span>New Project</span>
    </div>
    """, unsafe_allow_html=True)

def render_chats_section():
    """Render the recent chats section"""
    st.markdown('<div class="section-header">Recent Chats</div>', unsafe_allow_html=True)
    
    # Display recent chats
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history[:10]):  # Show last 10
            chat_title = chat.get('title', f'Chat {i+1}')
            chat_time = chat.get('timestamp', '')
            
            # Use consistent chat-item styling
            st.markdown(f"""
            <div class="chat-item" onclick="window.location.reload()">
                {chat_title}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            No recent chats
        </div>
        """, unsafe_allow_html=True)

def render_tools_section():
    """Render the tools section"""
    st.markdown('<div class="section-header">Tools</div>', unsafe_allow_html=True)
    
    # List Manager with actual functionality
    if st.button("List Manager", key="tool_list_manager", use_container_width=True):
        st.session_state.current_tool = "list_manager"
        st.session_state.show_list_manager = True
        st.rerun()
    
    # If List Manager is selected, show saved lists
    if st.session_state.get("show_list_manager"):
        from .list_manager import ListManagerUI
        list_manager = ListManagerUI()
        with st.container():
            list_manager.render_list_manager()
    
    # Other tools (placeholders for now)
    tools = [
        {"name": "Agents", "key": "agents"},
        {"name": "Campaigns", "key": "campaigns"},
        {"name": "A/B Tests", "key": "ab_tests"}
    ]
    
    for tool in tools:
        if st.button(f"{tool['name']}", key=f"tool_{tool['key']}", use_container_width=True):
            st.session_state.current_tool = tool['key']
            st.info(f"{tool['name']} coming soon!")

def toggle_sidebar():
    """Toggle sidebar visibility"""
    st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded

def add_chat_to_history(title: str, messages: List[Dict]):
    """Add a chat to the history"""
    chat_id = f"chat_{datetime.now().timestamp()}"
    chat_entry = {
        'id': chat_id,
        'title': title,
        'messages': messages,
        'timestamp': datetime.now().isoformat(),
        'project': st.session_state.current_project
    }
    
    # Add to chat history
    st.session_state.chat_history.insert(0, chat_entry)
    
    # Add to current project
    if st.session_state.current_project in st.session_state.projects:
        st.session_state.projects[st.session_state.current_project].insert(0, {
            'id': chat_id,
            'title': title
        })
    
    # Limit history to 50 chats
    if len(st.session_state.chat_history) > 50:
        st.session_state.chat_history = st.session_state.chat_history[:50]
    
    return chat_id

def get_current_chat():
    """Get the current chat by ID"""
    if st.session_state.current_chat_id:
        for chat in st.session_state.chat_history:
            if chat['id'] == st.session_state.current_chat_id:
                return chat
    return None

def create_new_chat():
    """Create a new chat session"""
    st.session_state.current_chat_id = None
    st.session_state.messages = []
    st.rerun()