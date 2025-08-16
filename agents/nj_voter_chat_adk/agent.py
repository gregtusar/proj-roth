from typing import Any, Dict
from google.adk.agents import Agent
from google.adk.tools import Tool

from .config import MODEL, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool

_bq_tool = BigQueryReadOnlyTool()

class BQToolAdapter(Tool):
    name = _bq_tool.name
    description = _bq_tool.description
    def run(self, **kwargs) -> Dict[str, Any]:
        sql = kwargs.get("sql") or kwargs.get("query") or ""
        return _bq_tool.run(sql)

class NJVoterChatAgent(Agent):
    def __init__(self):
        super().__init__(model=MODEL, system_instruction=SYSTEM_PROMPT, tools=[BQToolAdapter()])
