from typing import Any, Dict
import asyncio
import inspect
import time
import os
from google.adk.agents import Agent
from google.adk.runners import Runner

from .config import MODEL, PROJECT_ID, REGION, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool

_bq_tool = BigQueryReadOnlyTool()

def bigquery_select(sql: str) -> Dict[str, Any]:
    """Executes read-only SELECT queries on approved BigQuery tables.
    
    Args:
        sql (str): The SQL query to execute. Must be a SELECT query against approved tables.
        
    Returns:
        Dict[str, Any]: Query results including rows, row_count, truncated flag, elapsed time, and original SQL.
    """
    return _bq_tool.run(sql)

class NJVoterChatAgent(Agent):
    def __init__(self):
        import os
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = REGION
        
        print(f"[DEBUG] Initializing agent with instruction: {SYSTEM_PROMPT[:100]}...")
        super().__init__(name="nj_voter_chat", model=MODEL, tools=[bigquery_select], instruction=SYSTEM_PROMPT)
        print(f"[DEBUG] Agent initialized successfully with instruction parameter")
        self._initialize_services()
    
    def _initialize_services(self):
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
        from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
        from google.adk.runners import Runner
        
        self._session_service = InMemorySessionService()
        self._memory_service = InMemoryMemoryService()
        self._artifact_service = InMemoryArtifactService()
        self._runner = Runner(
            app_name="nj_voter_chat",
            agent=self,
            session_service=self._session_service,
            memory_service=self._memory_service,
            artifact_service=self._artifact_service
        )
        self._user_id = "streamlit_user"
        self._session_id = None

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
            from google.adk.agents.run_config import RunConfig
            from google.genai import types
            
            if not self._session_id:
                self._session_id = f"session_{int(time.time())}"
                session = _run_asyncio(self._session_service.create_session(
                    app_name="nj_voter_chat",
                    user_id=self._user_id,
                    session_id=self._session_id
                ))
                print(f"[DEBUG] Created new session: {self._session_id}")
            else:
                print(f"[DEBUG] Reusing existing session: {self._session_id}")
            
            if os.getenv("ADK_DEBUG_FALLBACK", "false").lower() == "true":
                combined_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
                message_content = types.Content(parts=[types.Part(text=combined_prompt)])
                print(f"[DEBUG] Using fallback combined prompt: {combined_prompt[:200]}...")
            else:
                message_content = types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
                print(f"[DEBUG] User prompt being sent with proper types.Content: {prompt[:200]}...")
            
            print(f"[DEBUG] Message content structure: {message_content}")
            print(f"[DEBUG] Session ID: {self._session_id}, User ID: {self._user_id}")
            
            print(f"[DEBUG] About to call runner.run_async with proper types.Content")
            run_config = RunConfig()
            agen = self._runner.run_async(
                user_id=self._user_id,
                session_id=self._session_id,
                new_message=message_content,
                run_config=run_config
            )
            print(f"[DEBUG] Runner.run_async returned: {type(agen)}")
            
            if inspect.isasyncgen(agen):
                result = _run_asyncio(_consume_async_gen(agen))
            else:
                result = agen
            
            if hasattr(result, 'content') and hasattr(result.content, 'parts'):
                print(f"[DEBUG] Result has content with {len(result.content.parts)} parts")
                text_parts = []
                for i, part in enumerate(result.content.parts):
                    print(f"[DEBUG] Part {i}: has_text={hasattr(part, 'text')}, text_length={len(part.text) if hasattr(part, 'text') and part.text else 0}")
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                if text_parts:
                    final_response = '\n'.join(text_parts)
                    print(f"[DEBUG] Extracted text response: {final_response[:200]}...")
                    print(f"[DEBUG] Response indicates system instruction awareness: {'data assistant' in final_response.lower() or 'bigquery' in final_response.lower()}")
                    return final_response
                else:
                    print(f"[WARNING] No text content found in response parts: {result.content.parts}")
                    return "No response content available."
            
            print(f"[WARNING] Unexpected response structure: {type(result)}")
            return str(result)
            
        except Exception as e:
            print(f"[ERROR] ADK Runner invocation failed: {e}")
            raise RuntimeError(
                f"Unable to invoke ADK agent using proper Runner patterns: {e}. "
                "This indicates a fundamental issue with ADK integration. "
                "Please check ADK installation and dependencies."
            )

    def __call__(self, prompt: str):
        """Direct Agent invocation bypassing Runner - matches travel-concierge pattern"""
        print(f"[DEBUG] NJVoterChatAgent.__call__ -> direct agent invocation")
        print(f"[DEBUG] User prompt: {prompt[:200]}...")
        
        try:
            from google.genai import types
            message = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
            
            result = super().generate_content([message])
            
            if hasattr(result, 'text') and result.text:
                print(f"[DEBUG] Direct agent response: {result.text[:200]}...")
                return result.text
            elif hasattr(result, 'content') and hasattr(result.content, 'parts'):
                text_parts = []
                for part in result.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    response = '\n'.join(text_parts)
                    print(f"[DEBUG] Direct agent response: {response[:200]}...")
                    return response
            
            print(f"[WARNING] Unexpected direct agent response structure: {type(result)}")
            return str(result)
            
        except Exception as e:
            print(f"[ERROR] Direct agent invocation failed: {e}")
            print(f"[DEBUG] Falling back to Runner approach")
            return self.chat(prompt)
    
    def invoke(self, prompt: str):
        """Alternative invocation method"""
        return self.__call__(prompt)
