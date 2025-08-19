"""
Main Streamlit app with authentication wrapper
"""
import streamlit as st
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.nj_voter_chat_adk.auth import check_authentication, GoogleAuthenticator
from agents.nj_voter_chat_adk.pages.login import show_login_page

# Set page config first
st.set_page_config(
    page_title="Greywolf Analytics", 
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check authentication
if not check_authentication():
    show_login_page()
else:
    # Import and run the main app
    from agents.nj_voter_chat_adk import app_streamlit
    # The main app will run automatically on import