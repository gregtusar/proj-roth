from typing import Any, Dict
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
    def chat(self, prompt: str):
        if hasattr(self, "__call__"):
            return self.__call__(prompt)
        if hasattr(self, "run"):
            return self.run(prompt)
        if hasattr(self, "respond"):
            return self.respond(prompt)
        raise AttributeError("Agent does not support chat; no compatible invoke method found.")

        super().__init__(name="nj_voter_chat", model=MODEL, tools=[BQToolAdapter()])
