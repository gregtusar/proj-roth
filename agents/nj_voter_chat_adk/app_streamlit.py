import streamlit as st
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
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
    page_title="NJ Voter Chat (ADK)", 
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
nj_theme_css = """
<style>
/* Light mode background */
.stApp {
    background-color: #FFFFFF;
}

/* Black text for headers */
h1, h2, h3 {
    color: #000000 !important;
    font-weight: 600;
}

/* Custom title styling */
.main-title {
    color: #000000;
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: #666666;
    text-align: center;
    font-style: italic;
    margin-bottom: 2rem;
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

/* Input styling */
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

st.markdown('<h1 class="main-title">🏛️ New Jersey Voter Data Chat</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by Google Gemini & BigQuery • Garden State Analytics</p>', unsafe_allow_html=True)

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
