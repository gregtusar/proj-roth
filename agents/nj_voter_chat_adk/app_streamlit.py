import streamlit as st
from .agent import NJVoterChatAgent

st.set_page_config(page_title="NJ Voter Chat (ADK)", layout="wide")
if "agent" not in st.session_state:
    st.session_state.agent = NJVoterChatAgent()
if "history" not in st.session_state:
    st.session_state.history = []

st.title("NJ Voter Chat (Gemini + BigQuery)")

for role, content in st.session_state.history:
    with st.chat_message(role):
        st.markdown(content)

prompt = st.chat_input("Ask a question about NJ voter data...")
if prompt:
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    resp = st.session_state.agent.chat(prompt)
    answer = getattr(resp, "text", "")
    st.session_state.history.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)
        tool_payload = getattr(resp, "tool_output", None) or {}
        rows = tool_payload.get("rows")
        if rows:
            st.dataframe(rows)
