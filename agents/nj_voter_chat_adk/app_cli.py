# Suppress known harmless warnings before importing other modules
from agents.nj_voter_chat_adk import suppress_warnings

import json
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


def main():
    agent = NJVoterChatAgent()
    print("NJ Voter Chat (ADK) - type 'exit' to quit.")
    while True:
        try:
            q = input("\n> ").strip()
        except EOFError:
            break
        if not q or q.lower() in {"exit", "quit"}:
            break
        resp = _agent_invoke(agent, q)
        
        # Handle different response types
        if isinstance(resp, str):
            # Direct string response
            print("\nAssistant:\n" + resp)
        elif hasattr(resp, "text"):
            # Object with text attribute
            print("\nAssistant:\n" + str(resp.text))
        elif hasattr(resp, "content"):
            # ADK response with content
            if hasattr(resp.content, "parts"):
                text_parts = []
                for part in resp.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    print("\nAssistant:\n" + '\n'.join(text_parts))
            else:
                print("\nAssistant:\n" + str(resp.content))
        else:
            # Fallback to string representation
            print("\nAssistant:\n" + str(resp))
        
        # Check for tool output (if present)
        tool_payload = getattr(resp, "tool_output", None) or {}
        rows = tool_payload.get("rows")
        if rows:
            print(f"\nRows returned: {len(rows)} (showing up to 10)")
            for r in rows[:10]:
                print(json.dumps(r, ensure_ascii=False))
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
