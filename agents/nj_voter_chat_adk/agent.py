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
        if hasattr(self, "run_async"):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                return asyncio.ensure_future(self.run_async(prompt))
            else:
                return asyncio.run(self.run_async(prompt))
        if hasattr(self, "run_live"):
            return self.run_live(prompt)
        if hasattr(self, "__call__"):
            return self(prompt)
        if hasattr(self, "invoke"):
            return self.invoke(prompt)
        if hasattr(self, "run"):
            return self.run(prompt)
        if hasattr(self, "respond"):
            return self.respond(prompt)
        raise AttributeError("Agent does not support chat; no compatible invoke method found.")

    def chat(self, prompt: str):
        if hasattr(self, "__call__"):
            return self(prompt)
        if hasattr(self, "invoke"):
            return self.invoke(prompt)
        if hasattr(self, "run"):
            return self.run(prompt)
        if hasattr(self, "respond"):
            return self.respond(prompt)
        raise AttributeError("Agent does not support chat; no compatible invoke method found.")
