import streamlit as st
import sys
import os

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

/* Hamburger menu button for sidebar toggle */
.sidebar-toggle-btn {
    position: fixed;
    left: 1rem;
    top: 1rem;
    z-index: 1001;
    background: #FFFFFF;
    border: 1px solid #E2E2E2;
    border-radius: 8px;
    padding: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s;
}

.sidebar-toggle-btn:hover {
    background: #F6F6F6;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* When sidebar is visible, move the button */
[data-testid="stSidebar"][aria-expanded="true"] ~ .main .sidebar-toggle-btn {
    left: 295px;
}

/* Fixed header styling */
.fixed-header {
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    background-color: #FFFFFF;
    z-index: 999;
    padding: 1.5rem 0 0.5rem 0;
    border-bottom: 2px solid #E3F2FD;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
    text-align: center;
    max-width: 1200px;
    margin: 0 auto;
}

.logo-container {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
    margin-bottom: 0.5rem;
}

.logo-container img {
    width: 80px;
    height: 80px;
}

/* Black text for headers */
h1, h2, h3 {
    color: #000000 !important;
    font-weight: 600;
}

/* Custom title styling */
.main-title {
    color: #2C5282;
    text-align: center;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}

/* Add padding to main content to account for fixed header and footer */
.main-content {
    padding-top: 250px;
    padding-bottom: 100px;
    min-height: calc(100vh - 350px);
}

/* User info styling */
.user-info {
    position: fixed;
    top: 10px;
    right: 20px;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    padding: 5px 10px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.user-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
}

/* Chat message styling */
.stChatMessage {
    background-color: #F8F9FA;
    border-left: 4px solid #0066CC;
    border-radius: 8px;
    margin: 0.5rem 0;
    color: #000000 !important;
}

/* Ensure all chat message content is black */
.stChatMessage p, .stChatMessage div, .stChatMessage span {
    color: #000000 !important;
}

/* Make sure markdown content in chat messages is black */
.stChatMessage .stMarkdown {
    color: #000000 !important;
}

/* Input styling - fixed at bottom */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #FFFFFF;
    padding: 1rem;
    border-top: 2px solid #E3F2FD;
    box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
    z-index: 998;
}

.stChatInput > div > div > input {
    border: 2px solid #E3F2FD;
    border-radius: 8px;
}

.stChatInput > div > div > input:focus {
    border-color: #0066CC;
    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
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

if "agent" not in st.session_state:
    st.session_state.agent = NJVoterChatAgent()
if "history" not in st.session_state:
    st.session_state.history = []
if "chat_saved" not in st.session_state:
    st.session_state.chat_saved = False

# User info and logout button in top right
if "user_info" in st.session_state:
    user_info = st.session_state["user_info"]
    user_id = user_info.get("google_id", user_info.get("id", "default_user"))
    user_email = user_info.get("email", "")
    user_name = user_info.get("full_name", user_email)
    user_picture = user_info.get("picture_url", "")
    
    # Set user context for list saving
    list_manager = ListManagerUI()
    list_manager.set_user_context(user_id, user_email)
    
    # Display user info in top right
    st.markdown(f"""
        <div class="user-info">
            {f'<img src="{user_picture}" class="user-avatar" alt="User" />' if user_picture else ''}
            <span>{user_name}</span>
        </div>
    """, unsafe_allow_html=True)
    
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

# Create fixed header with logo and title
import base64
from pathlib import Path

# Load and encode the logo
logo_path = Path(__file__).parent / "greywolf_logo.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_data}" alt="Greywolf Logo">'
else:
    logo_html = '🐺'  # Fallback if logo not found

header_html = f"""
<div class="fixed-header">
    <div class="header-content">
        <div class="logo-container">
            {logo_html}
        </div>
        <h1 class="main-title">Greywolf Analytica</h1>
    </div>
</div>
<div class="main-content">
"""

st.markdown(header_html, unsafe_allow_html=True)

# Add hamburger menu button for sidebar toggle
st.markdown("""
<button class="sidebar-toggle-btn" onclick="
    const sidebar = document.querySelector('[data-testid=stSidebar]');
    const expandedAttr = sidebar.getAttribute('aria-expanded');
    if (expandedAttr === 'true') {
        // Close sidebar
        document.querySelector('[data-testid=collapsedControl] button').click();
    } else {
        // Open sidebar
        document.querySelector('[data-testid=collapsedControl] button').click();
    }
">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B5D7C" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
</button>
""", unsafe_allow_html=True)

for role, content in st.session_state.history:
    with st.chat_message(role):
        st.markdown(content)

prompt = st.chat_input("Ask a question about New Jersey voter data... 🗳️")
if prompt:
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
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
        
        with st.chat_message("assistant"):
            st.markdown(answer)
            if rows:
                st.dataframe(rows)
    except Exception as e:
        st.session_state.history.append(("assistant", f"Error: {e}"))
        with st.chat_message("assistant"):
            st.exception(e)
        import traceback
        print("[ERROR] Exception during agent invocation:\n", traceback.format_exc())

# Render list modal if needed
if st.session_state.get("show_list_modal"):
    list_manager.render_list_modal()

# Close the main-content div
st.markdown("</div>", unsafe_allow_html=True)
