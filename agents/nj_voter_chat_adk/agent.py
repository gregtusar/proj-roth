from typing import Any, Dict
import asyncio
import inspect
import time
from google.adk.agents import Agent
from google.adk.runners import Runner

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
        def _run_asyncio(coro):
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                new_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(new_loop)
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
                    asyncio.set_event_loop(loop)
            else:
                return asyncio.run(coro)

        async def _consume_async_gen(agen):
            last = None
            async for chunk in agen:
                last = chunk
            return last

        try:
            print("[DEBUG] NJVoterChatAgent.chat -> using proper ADK Runner invocation")
            from google.adk.sessions.in_memory_session_service import InMemorySessionService
            from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
            from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
            from google.adk.agents.run_config import RunConfig
            from google.genai import types
            import uuid
            
            session_service = InMemorySessionService()
            memory_service = InMemoryMemoryService()
            artifact_service = InMemoryArtifactService()
            
            runner = Runner(
                app_name="nj_voter_chat",
                agent=self,
                session_service=session_service,
                memory_service=memory_service,
                artifact_service=artifact_service
            )
            
            user_id = "streamlit_user"
            session_id = f"session_{int(time.time())}"
            
            session = _run_asyncio(session_service.create_session(
                app_name="nj_voter_chat",
                user_id=user_id,
                session_id=session_id
            ))
            
            message_content = types.Content(parts=[types.Part(text=prompt)])
            
            agen = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message_content,
                run_config=RunConfig()
            )
            
            if inspect.isasyncgen(agen):
                return _run_asyncio(_consume_async_gen(agen))
            return agen
            
        except Exception as e:
            print(f"[ERROR] ADK Runner invocation failed: {e}")
            raise RuntimeError(
                f"Unable to invoke ADK agent using proper Runner patterns: {e}. "
                "This indicates a fundamental issue with ADK integration. "
                "Please check ADK installation and dependencies."
            )
