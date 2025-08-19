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
    page_title="Greywolf Analytics", 
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check authentication before proceeding
if not check_authentication():
    # Show login interface
    from agents.nj_voter_chat_adk.pages.login import show_login_page
    show_login_page()
    st.stop()
nj_theme_css = """
<style>
/* Light mode background */
.stApp {
    background-color: #FFFFFF;
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

# User info and logout button in top right
if "user_info" in st.session_state:
    user_info = st.session_state["user_info"]
    user_email = user_info.get("email", "")
    user_name = user_info.get("full_name", user_email)
    user_picture = user_info.get("picture_url", "")
    
    # Display user info in top right
    st.markdown(f"""
        <div class="user-info">
            {f'<img src="{user_picture}" class="user-avatar" alt="User" />' if user_picture else ''}
            <span>{user_name}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Add logout button in sidebar
    with st.sidebar:
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
        <h1 class="main-title">Greywolf Analytics, LLC</h1>
    </div>
</div>
<div class="main-content">
"""

st.markdown(header_html, unsafe_allow_html=True)

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

# Close the main-content div
st.markdown("</div>", unsafe_allow_html=True)
