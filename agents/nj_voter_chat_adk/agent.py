from typing import Any, Dict
import asyncio
import inspect
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.agents.invocation_context import InvocationContext

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
            print("[DEBUG] NJVoterChatAgent.chat -> using Runner.run_async for proper ADK invocation")
            runner = Runner(agent=self)
            agen = runner.run_async(prompt)
            if inspect.isasyncgen(agen):
                return _run_asyncio(_consume_async_gen(agen))
            return agen
        except Exception as e:
            print(f"[ERROR] Runner.run_async failed: {e}")
            
        try:
            print("[DEBUG] NJVoterChatAgent.chat -> fallback to direct run_async with proper InvocationContext")
            from google.adk.agents.session import Session
            import uuid
            
            session = Session()
            context = InvocationContext(
                agent=self,
                session=session,
                invocation_id=str(uuid.uuid4()),
                input=prompt
            )
            agen = self.run_async(context)
            if inspect.isasyncgen(agen):
                return _run_asyncio(_consume_async_gen(agen))
            return agen
        except Exception as e:
            print(f"[ERROR] Direct run_async with InvocationContext failed: {e}")
            raise RuntimeError(
                f"Unable to invoke ADK agent: {e}. "
                "This agent requires proper ADK framework invocation patterns. "
                "Consider using 'adk web' or 'adk run' commands instead of direct method calls."
            )
