import streamlit as st
import sys
import os
import time
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Suppress known harmless warnings before importing other modules
from agents.nj_voter_chat_adk import suppress_warnings

from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
from agents.nj_voter_chat_adk.auth import check_authentication, GoogleAuthenticator
from agents.nj_voter_chat_adk.styles.base_design import apply_base_design, create_uber_card, create_metric_card
from agents.nj_voter_chat_adk.components.sidebar import render_sidebar, add_chat_to_history, get_current_chat
from agents.nj_voter_chat_adk.components.list_manager import ListManagerUI
def _agent_invoke(agent, prompt: str):
    if hasattr(agent, "chat"):
        return agent.chat(prompt)
    if hasattr(agent, "__call__"):
        return agent(prompt)
    if hasattr(agent, "invoke"):
        return agent.invoke(prompt)
    if hasattr(agent, "run"):
        return agent.run(prompt)
    if hasattr(agent, "respond"):
        return agent.respond(prompt)
    raise AttributeError("Agent does not support invocation")


st.set_page_config(
    page_title="Greywolf Analytica", 
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply Uber Base design system
apply_base_design()

# Check authentication before proceeding
if not check_authentication():
    # Show login interface
    from agents.nj_voter_chat_adk.pages.login import show_login_page
    show_login_page()
    st.stop()
# Custom NJ theme CSS (now integrated with Base design)
nj_theme_css = """
<style>
/* Extends Base design system with custom NJ theme */
/* Override text colors to use wolf blue */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #3B5D7C !important;
}

/* Removed custom hamburger menu - using Streamlit's native toggle */

/* Logo in top left corner - positioned next to Streamlit's toggle */
.logo-top-left {
    position: fixed;
    left: 65px;
    top: 0.75rem;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    background: white;
    border-radius: 8px;
    padding: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo-top-left img {
    width: 36px;
    height: 36px;
    object-fit: contain;
}

/* Black text for headers */
h1, h2, h3 {
    color: #000000 !important;
    font-weight: 600;
}

/* Keep Streamlit's sidebar toggle visible but style it */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: auto !important;
    z-index: 999 !important;
}

/* Style the sidebar toggle button - both collapsed and expanded states */
button[data-testid="collapsedControl"], 
button[data-testid="expandedControl"] {
    top: 1rem !important;
    left: 1rem !important;
    color: #3B5D7C !important;
    z-index: 1000 !important;
    position: fixed !important;
}

/* Keep the expanded control visible when sidebar is open */
button[data-testid="expandedControl"] {
    display: block !important;
    visibility: visible !important;
}

/* Adjust main view */
.main .block-container {
    padding-top: 1rem !important;
    max-width: 100% !important;
}

/* Style sidebar buttons to match interface */
.stSidebar button {
    background: transparent !important;
    border: none !important;
    color: #666666 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    text-align: left !important;
    padding: 8px 12px !important;
    transition: background-color 0.2s !important;
}

.stSidebar button:hover {
    background-color: rgba(0, 0, 0, 0.05) !important;
    border-radius: 6px !important;
}

/* Style Recent Chats header to match */
.stSidebar h3, .stSidebar .sidebar-section-header {
    color: #666666 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    margin: 1rem 0 0.5rem 0 !important;
}

/* Style the Default Project text */
.stSidebar .project-name {
    color: #666666 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
}

/* Hide the decoration at the top */
[data-testid="stDecoration"] {
    display: none !important;
}


/* Make code blocks wrap text instead of horizontal scroll */
div[data-testid="stCode"] {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

div[data-testid="stCode"] pre {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

div[data-testid="stCode"] code {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Add padding to main content - no header now */
.main-content {
    padding-top: 2rem;
    padding-bottom: 100px;
    min-height: calc(100vh - 132px);
    max-width: 768px;
    margin-left: auto;
    margin-right: auto;
    padding-left: 0;
    padding-right: 0;
}

/* User info styling - bottom left */
.user-info {
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 997;
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    padding: 8px 12px;
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-size: 14px;
    color: #333;
}

.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid #E2E2E2;
}

/* Chat message styling - ChatGPT-like appearance */
.stChatMessage {
    background-color: transparent;
    border: none;
    border-radius: 0;
    margin: 1rem 0;
    padding: 0.75rem 0;
    color: #000000 !important;
    max-width: 100%;
}

.stChatMessage[data-testid="stChatMessageContainer-assistant"] {
    background-color: #F7F7F8;
    border-radius: 8px;
    padding: 1rem;
}

/* Ensure all content is properly aligned */
[data-testid="stVerticalBlock"] {
    max-width: 768px;
    margin-left: auto;
    margin-right: auto;
}

/* Align spinner message */
.stSpinner {
    text-align: left;
    margin-left: 0;
    padding-left: 0;
}

/* Ensure all chat message content is black */
.stChatMessage p, .stChatMessage div, .stChatMessage span {
    color: #000000 !important;
}

/* Make sure markdown content in chat messages is black */
.stChatMessage .stMarkdown {
    color: #000000 !important;
}

/* Input styling - ChatGPT-like compact design */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 768px;
    background-color: transparent;
    padding: 1rem 0 1.5rem 0;
    z-index: 998;
}

.stChatInput > div {
    background-color: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    padding: 0.5rem;
}

.stChatInput > div > div {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.stChatInput > div > div > input {
    border: 2px solid #3B5D7C;  /* Changed to wolf blue color */
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 15px;
    background-color: #F7F7F8;
    transition: all 0.2s;
}

.stChatInput > div > div > input:focus {
    border-color: #3B5D7C;  /* Keep the same blue on focus */
    background-color: #FFFFFF;
    box-shadow: 0 0 0 3px rgba(59, 93, 124, 0.2);  /* Blue shadow matching our theme */
    outline: none;
}

.stChatInput > div > div > input::placeholder {
    color: #8E8E93;
}


/* Loading spinner styling */
.stSpinner {
    color: #0066CC;
}

/* Button styling */
.stButton > button {
    background-color: #0066CC;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: #0052A3;
}

/* Dataframe styling */
.stDataFrame {
    border: 1px solid #E3F2FD;
    border-radius: 8px;
}
</style>
"""

st.markdown(nj_theme_css, unsafe_allow_html=True)

# Import for logo handling - do this early
import base64
from pathlib import Path

# Load and encode the logo - use absolute path resolution
try:
    logo_path = Path(__file__).parent / "greywolf_logo.png"
    if logo_path.exists() and logo_path.is_file():
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_data}" alt="Wolf" style="width: 36px; height: 36px; object-fit: contain;">'
        st.session_state.wolf_icon_data = logo_data  # Store for later use
        print(f"[DEBUG] Logo loaded successfully from {logo_path}")
    else:
        # Use emoji fallback
        logo_html = '<span style="font-size: 28px;">🐺</span>'
        st.session_state.wolf_icon_data = None
        print(f"[DEBUG] Logo file not found at {logo_path}, using emoji")
except Exception as e:
    logo_html = '<span style="font-size: 28px;">🐺</span>'
    st.session_state.wolf_icon_data = None
    print(f"[DEBUG] Error loading logo: {e}")

# Display logo in top left corner next to hamburger menu
st.markdown(f"""
<div class="logo-top-left">
    {logo_html}
</div>
""", unsafe_allow_html=True)

if "agent" not in st.session_state:
    st.session_state.agent = NJVoterChatAgent()
if "history" not in st.session_state:
    st.session_state.history = []
if "chat_saved" not in st.session_state:
    st.session_state.chat_saved = False

# Initialize list manager
list_manager = ListManagerUI()

# User info and logout button in top right
if "user_info" in st.session_state:
    user_info = st.session_state["user_info"]
    user_id = user_info.get("google_id", user_info.get("id", "default_user"))
    user_email = user_info.get("email", "")
    user_name = user_info.get("full_name", user_email)
    user_picture = user_info.get("picture_url", "")
    
    # Debug logging for profile picture
    if user_picture:
        print(f"[DEBUG] User profile picture URL: {user_picture}")
    else:
        print(f"[DEBUG] No profile picture URL found in user_info: {user_info.keys()}")
    
    # Set user context for list saving
    list_manager.set_user_context(user_id, user_email)
    
    # Display user info in bottom left - always use initial since Google photos have CORS issues
    with st.container():
        # Create a placeholder for user info at bottom left using CSS
        user_info_placeholder = st.empty()
        # Always use initial - Google profile pictures have CORS/auth issues in iframes
        initial = user_name[0].upper() if user_name else "U"
        user_info_placeholder.markdown(
            f'''<div class="user-info">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #3B5D7C; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                    {initial}
                </div>
                <span>{user_name}</span>
            </div>''',
            unsafe_allow_html=True
        )
    
    # Render custom sidebar with navigation
    render_sidebar()
    
    # Add logout button at bottom of sidebar
    with st.sidebar:
        st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            auth = GoogleAuthenticator()
            auth.logout()
            st.rerun()


# Start main content area
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Remove the hamburger menu entirely - Streamlit's sidebar works better without custom controls
# The sidebar can be toggled using Streamlit's built-in arrow button

# Wolf icon data should already be loaded above

for idx, (role, content) in enumerate(st.session_state.history):
    # Use wolf icon for user messages, default robot for assistant
    if role == "user" and st.session_state.wolf_icon_data:
        with st.chat_message(role, avatar=f"data:image/png;base64,{st.session_state.wolf_icon_data}"):
            st.markdown(content)
    else:
        with st.chat_message(role):
            if role == "assistant":
                # Display assistant responses in a code block with copy button
                # Text wrapping is handled by global CSS
                st.code(content, language="markdown")
            else:
                st.markdown(content)

prompt = st.chat_input("Ask a question about New Jersey voter data... 🗳️")
if prompt:
    st.session_state.history.append(("user", prompt))
    # Use wolf icon for user messages
    if st.session_state.get('wolf_icon_data'):
        with st.chat_message("user", avatar=f"data:image/png;base64,{st.session_state.wolf_icon_data}"):
            st.markdown(prompt)
    else:
        with st.chat_message("user"):
            st.markdown(prompt)
    try:
        # Use a container to ensure spinner is aligned
        spinner_container = st.container()
        with spinner_container:
            with st.spinner("🔍 Analyzing New Jersey voter data..."):
                resp = _agent_invoke(st.session_state.agent, prompt)
        print("[DEBUG] Response type:", type(resp))
        if resp is not None:
            try:
                print("[DEBUG] Response dir():", [a for a in dir(resp) if not a.startswith("_")][:50])
                if hasattr(resp, "__dict__"):
                    print("[DEBUG] Response __dict__ (truncated):", {k: str(v)[:200] for k, v in resp.__dict__.items()})
            except Exception as _e:
                print("[DEBUG] Failed to introspect resp:", repr(_e))
        answer = ""
        rows = None
        if isinstance(resp, str):
            answer = resp
        elif resp is not None:
            if hasattr(resp, "text") and isinstance(getattr(resp, "text"), str):
                answer = getattr(resp, "text")
            elif hasattr(resp, "output_text") and isinstance(getattr(resp, "output_text"), str):
                answer = getattr(resp, "output_text")
            elif hasattr(resp, "content"):
                try:
                    answer = str(getattr(resp, "content"))
                except Exception:
                    pass
            tool_payload = getattr(resp, "tool_output", None)
            if tool_payload is None and hasattr(resp, "data"):
                tool_payload = getattr(resp, "data")
            if isinstance(tool_payload, dict):
                rows = tool_payload.get("rows")
        if not answer:
            answer = "(No assistant text returned. See logs for details.)"
        st.session_state.history.append(("assistant", answer))
        
        # Save chat to history if it has meaningful content
        if len(st.session_state.history) > 0 and not st.session_state.get('chat_saved'):
            # Extract first few words of the prompt as title
            title = prompt[:50] + "..." if len(prompt) > 50 else prompt
            chat_id = add_chat_to_history(title, st.session_state.history)
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_saved = True
        
        # Use default robot icon for assistant messages
        with st.chat_message("assistant"):
            # Display response in a code block with copy button
            # Text wrapping is handled by global CSS
            st.code(answer, language="markdown")
            if rows:
                st.dataframe(rows)
    except Exception as e:
        st.session_state.history.append(("assistant", f"Error: {e}"))
        # Use default robot icon for error messages
        with st.chat_message("assistant"):
            st.exception(e)
        import traceback
        print("[ERROR] Exception during agent invocation:\n", traceback.format_exc())

# Render list modal using Streamlit's dialog feature
if st.session_state.get("show_list_modal"):
    @st.dialog("📋 Voter List Details", width="large")
    def show_list_dialog():
        list_manager.render_list_modal_content()
    show_list_dialog()

# Close the main-content div
st.markdown("</div>", unsafe_allow_html=True)
