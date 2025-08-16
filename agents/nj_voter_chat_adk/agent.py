from typing import Any, Dict
try:
    from adk import Agent, Tool
except Exception:
    Agent = object
    class Tool:  # type: ignore
        name = ""
        description = ""
        def run(self, **kwargs):  # type: ignore
            return {}

from .config import MODEL, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool

_bq_tool = BigQueryReadOnlyTool()

class BQToolAdapter(Tool):
    name = _bq_tool.name
    description = _bq_tool.description
    def run(self, **kwargs) -> Dict[str, Any]:
        sql = kwargs.get("sql") or kwargs.get("query") or ""
        return _bq_tool.run(sql)

class NJVoterChatAgent(Agent):  # type: ignore
    def __init__(self):
        try:
            super().__init__(model=MODEL, system_instruction=SYSTEM_PROMPT, tools=[BQToolAdapter()])  # type: ignore
        except Exception:
            self._fallback = True

    def chat(self, prompt: str):
        try:
            return super().chat(prompt)  # type: ignore
        except Exception:
            result = {"text": "ADK not available in this environment."}
            class Resp:
                def __init__(self, t): self.text = t; self.tool_output = {}
            return Resp(result["text"])
