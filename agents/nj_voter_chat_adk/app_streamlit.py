import streamlit as st
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
    try:
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
