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
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .google-btn {
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
            cursor: pointer;
            transition: background-color 0.3s, box-shadow 0.3s;
            text-decoration: none;
            margin: 20px auto;
            display: block;
            width: fit-content;
        }
        .google-btn:hover {
            background-color: #f8f9fa;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
        }
        .google-icon {
            margin-right: 12px;
            width: 18px;
            height: 18px;
        }
        .title-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 1rem;
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
                st.markdown("🗳️", unsafe_allow_html=True)
        else:
            # Fallback to emoji if logo not found
            st.markdown("# 🗳️", unsafe_allow_html=True)
        
        st.markdown("# NJ Voter Chat")
        st.markdown("### Congressional District 07 Analysis")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Login description
        st.markdown("""
        Welcome to the NJ Voter Chat system. This application provides 
        intelligent analysis of voter registration data for New Jersey's 
        Congressional District 07.
        
        Please sign in with your Google account to continue.
        """)
        
        # Google Sign-In button
        auth = GoogleAuthenticator()
        auth_url = auth.get_google_auth_url()
        
        # Create Google sign-in button with logo
        google_logo_svg = """
        <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="google-icon">
            <g>
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </g>
        </svg>
        """
        
        st.markdown(f"""
            <a href="{auth_url}" class="google-btn">
                {google_logo_svg}
                Continue with Google
            </a>
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