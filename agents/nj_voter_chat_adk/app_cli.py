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
        text = getattr(resp, "text", "")
        print("\nAssistant:\n" + str(text))
        tool_payload = getattr(resp, "tool_output", None) or {}
        rows = tool_payload.get("rows")
        if rows:
            print(f"\nRows returned: {len(rows)} (showing up to 10)")
            for r in rows[:10]:
                print(json.dumps(r, ensure_ascii=False))
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
