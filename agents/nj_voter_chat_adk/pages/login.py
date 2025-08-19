"""
Login page for NJ Voter Chat with Google OAuth
"""
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import GoogleAuthenticator, check_authentication
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def show_login_page():
    """Display the login page with Google sign-in"""
    
    # Page configuration
    st.set_page_config(
        page_title="NJ Voter Chat - Login",
        page_icon="🗳️",
        layout="centered"
    )
    
    # Custom CSS for login page
    st.markdown("""
        <style>
        .main {
            padding-top: 3rem;
        }
        .title-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Check if returning from OAuth callback
    query_params = st.query_params
    if "code" in query_params:
        handle_oauth_callback(query_params["code"])
        return
    
    # Check if already authenticated
    if check_authentication():
        st.success("You are already logged in!")
        if st.button("Go to Chat"):
            st.switch_page("app_streamlit.py")
        return
    
    # Display login interface
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo and title
        st.markdown('<div class="title-container">', unsafe_allow_html=True)
        
        # Try to load logo
        logo_path = "greywolf_logo.png"
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                st.image(logo, width=80)
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")
                st.markdown("# 🐺", unsafe_allow_html=True)
        else:
            # Fallback to wolf emoji if logo not found
            st.markdown("# 🐺", unsafe_allow_html=True)
        
        st.markdown("# Greywolf Analytica")
        st.markdown("### NJ Voter Data Intelligence Platform")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Login description
        st.markdown("""
        Welcome to Greywolf Analytica's voter intelligence platform. 
        This application provides advanced analysis of voter registration 
        data for New Jersey's Congressional District 07.
        
        Please sign in with your Google account to continue.
        """)
        
        # Google Sign-In button
        auth = GoogleAuthenticator()
        auth_url = auth.get_google_auth_url()
        
        # Create Google sign-in button with simpler approach
        st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <a href="{auth_url}" style="
                    display: inline-flex;
                    align-items: center;
                    padding: 12px 24px;
                    background-color: white;
                    color: #3c4043;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    font-family: 'Roboto', sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    text-decoration: none;
                    transition: background-color 0.3s, box-shadow 0.3s;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                ">
                    <img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPCEtLSBHZW5lcmF0b3I6IEFkb2JlIElsbHVzdHJhdG9yIDI1LjAuMCwgU1ZHIEV4cG9ydCBQbHVnLUluIC4gU1ZHIFZlcnNpb246IDYuMDAgQnVpbGQgMCkgIC0tPgo8c3ZnIHZlcnNpb249IjEuMSIgaWQ9IkxheWVyXzEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHg9IjBweCIgeT0iMHB4IgoJIHZpZXdCb3g9IjAgMCA0OCA0OCIgc3R5bGU9ImVuYWJsZS1iYWNrZ3JvdW5kOm5ldyAwIDAgNDggNDg7IiB4bWw6c3BhY2U9InByZXNlcnZlIj4KPHN0eWxlIHR5cGU9InRleHQvY3NzIj4KCS5zdDB7ZmlsbDojRUE0MzM1O30KCS5zdDF7ZmlsbDojNDI4NUY0O30KCS5zdDJ7ZmlsbDojRkJCQzA1O30KCS5zdDN7ZmlsbDojMzRBODUzO30KPC9zdHlsZT4KPGc+Cgk8cGF0aCBjbGFzcz0ic3QwIiBkPSJNMjQsOS41YzMuNTQsMCw2LjcxLDEuMjIsOS4yMSwzLjZsNi44NS02Ljg1QzM1LjksMi4zOCwzMC40NywwLDI0LDBDMTQuNjIsMCw2LjUxLDUuMzgsMi41NiwxMy4yMmw3Ljk4LDYuMTkKCQlDMTIuNDMsMTMuNzIsMTcuNzQsOS41LDI0LDkuNXoiLz4KCTxwYXRoIGNsYXNzPSJzdDEiIGQ9Ik00Ni45OCwyNC41NWMwLTEuNTctMC4xNS0zLjA5LTAuMzgtNC41NUgyNHY5LjAyaDEyLjk0Yy0wLjU4LDIuOTYtMi4yNiw1LjQ4LTQuNzgsNy4xOGw3LjczLDYKCQlDNDQuNDksMzguMzcsNDcuMDcsMzEuOTEsNDYuOTgsMjQuNTV6Ii8+Cgk8cGF0aCBjbGFzcz0ic3QyIiBkPSJNMTAuNTMsMjguNTljLTAuNDgtMS40NS0wLjc2LTIuOTktMC43Ni00LjU5czAuMjctMy4xNCwwLjc2LTQuNTlsLTcuOTgtNi4xOUMwLjkyLDE2LjQ2LDAsMjAuMTIsMCwyNAoJCWMwLDMuODgsMC45Miw3LjU0LDIuNTYsMTAuNzhMMTAuNTMsMjguNTl6Ii8+Cgk8cGF0aCBjbGFzcz0ic3QzIiBkPSJNMjQsNDhjNi40OCwwLDExLjkzLTIuMTMsMTUuODktNS44MWwtNy43My02Yy0yLjE1LDEuNDUtNC45MiwyLjMtOC4xNiwyLjNjLTYuMjYsMC0xMS41Ny00LjIyLTEzLjQ3LTkuOTEKCQlsLTcuOTgsNi4xOUM2LjUxLDQyLjYyLDE0LjYyLDQ4LDI0LDQ4eiIvPgo8L2c+Cjwvc3ZnPgo=" 
                         style="width: 18px; height: 18px; margin-right: 12px;" 
                         alt="Google Logo"/>
                    Continue with Google
                </a>
            </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.caption("""
        By signing in, you agree to use this system responsibly and in 
        accordance with all applicable laws and regulations.
        """)


def handle_oauth_callback(code: str):
    """Handle the OAuth callback after user authorizes"""
    auth = GoogleAuthenticator()
    
    with st.spinner("Authenticating..."):
        # Get user info from OAuth
        user_info = auth.handle_callback(code)
        
        if not user_info:
            st.error("Authentication failed. Please try again.")
            st.warning("⚠️ Debug: Check Cloud Run logs for detailed error information")
            st.info("Run: `gcloud run logs read nj-voter-chat --limit=50 --project=proj-roth`")
            st.query_params.clear()
            return
        
        # Check if user is authorized
        if not auth.check_user_authorized(user_info["email"]):
            st.error(f"Access denied. Your email ({user_info['email']}) is not authorized to use this system.")
            st.info("Please contact an administrator to request access.")
            st.query_params.clear()
            return
        
        # Create or update user record
        user_id = auth.create_or_update_user(user_info)
        
        if not user_id:
            st.error("Failed to create user session. Please try again.")
            st.query_params.clear()
            return
        
        # Create access token
        access_token = auth.create_access_token(user_id, user_info["email"])
        
        # Store in session state
        st.session_state["access_token"] = access_token
        st.session_state["user_info"] = user_info
        st.session_state["authenticated"] = True
        
        # Clear query params
        st.query_params.clear()
        
        # Redirect to main app
        st.success(f"Welcome, {user_info.get('full_name', user_info['email'])}!")
        st.balloons()
        st.rerun()


if __name__ == "__main__":
    show_login_page()