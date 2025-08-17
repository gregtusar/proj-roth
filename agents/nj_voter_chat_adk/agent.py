from typing import Any, Dict
import asyncio
import inspect
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

        def _call_with_variants(method, prompt_text: str):
            variants = [
                ("(None, prompt)", lambda: method(None, prompt_text)),
                ("input=prompt", lambda: method(input=prompt_text)),
                ("prompt=prompt", lambda: method(prompt=prompt_text)),
            ]
            last_err = None
            for i, (name, attempt) in enumerate(variants, 1):
                try:
                    print(f"[DEBUG] Trying agent method call variant #{i}: {name}")
                    return attempt()
                except TypeError as te:
                    last_err = te
                    print(f"[DEBUG] Variant #{i} failed with TypeError: {te}")
                    continue
                except AttributeError as ae:
                    last_err = ae
                    print(f"[DEBUG] Variant #{i} failed with AttributeError: {ae}")
                    break
            if last_err:
                raise last_err
            raise RuntimeError("No viable method call variant succeeded")

        if hasattr(self, "run_live"):
            print("[DEBUG] NJVoterChatAgent.chat -> using run_live")
            try:
                res = _call_with_variants(self.run_live, prompt)
            except Exception as e:
                print("[WARN] run_live variants failed; falling back to run_async if available:", repr(e))
                res = None
            if res is not None:
                if inspect.isasyncgen(res):
                    try:
                        return _run_asyncio(_consume_async_gen(res))
                    except Exception as e:
                        print("[ERROR] NJVoterChatAgent.chat run_live asyncgen consume failed:", repr(e))
                        raise
                return res

        if hasattr(self, "run_async"):
            print("[DEBUG] NJVoterChatAgent.chat -> using run_async (no prompt arg; may be async generator)")
            try:
                agen = self.run_async()
                if inspect.isasyncgen(agen):
                    return _run_asyncio(_consume_async_gen(agen))
                return agen
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
