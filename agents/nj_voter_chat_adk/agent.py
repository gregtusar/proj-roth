from typing import Any, Dict
import asyncio
from google.adk.agents import Agent

from .config import MODEL
from .bigquery_tool import BigQueryReadOnlyTool

_bq_tool = BigQueryReadOnlyTool()

class BQToolAdapter:
    name = _bq_tool.name
    description = _bq_tool.description
    def run(self, **kwargs) -> Dict[str, Any]:
        sql = kwargs.get("sql") or kwargs.get("query") or ""
        return _bq_tool.run(sql)
    def __call__(self, **kwargs) -> Dict[str, Any]:
        return self.run(**kwargs)

class NJVoterChatAgent(Agent):
    def __init__(self):
        super().__init__(name="nj_voter_chat", model=MODEL, tools=[BQToolAdapter()])

    def chat(self, prompt: str):
        if hasattr(self, "run_live"):
            print("[DEBUG] NJVoterChatAgent.chat -> using run_live")
            return self.run_live(prompt)
        if hasattr(self, "run_async"):
            print("[DEBUG] NJVoterChatAgent.chat -> using run_async (async generator)")
            async def _consume():
                last = None
                agen = self.run_async(prompt)
                async for chunk in agen:
                    last = chunk
                return last
            try:
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        return new_loop.run_until_complete(_consume())
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(loop)
                else:
                    return asyncio.run(_consume())
            except Exception as e:
                print("[ERROR] NJVoterChatAgent.chat run_async failed:", repr(e))
                raise
        if hasattr(self, "__call__"):
            return self(prompt)
        if hasattr(self, "invoke"):
            return self.invoke(prompt)
        if hasattr(self, "run"):
            return self.run(prompt)
        if hasattr(self, "respond"):
            return self.respond(prompt)
        raise AttributeError("Agent does not support chat; no compatible invoke method found.")
