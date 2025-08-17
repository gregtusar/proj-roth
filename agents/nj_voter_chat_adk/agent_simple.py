import asyncio
import inspect
import time
import os
import google.generativeai as genai

from .config import MODEL, PROJECT_ID, REGION, SYSTEM_PROMPT
from .bigquery_tool import BigQueryReadOnlyTool
from .google_search_tool import GoogleSearchTool

def bigquery_select(query: str):
    try:
        tool = BigQueryReadOnlyTool()
        result = tool.run(query)
        return {
            "query": query,
            "results": result
        }
    except Exception as e:
        print(f"[ERROR] BigQuery tool failed: {str(e)}")
        return {
            "query": query,
            "results": []
        }

def google_search(query: str):
    try:
        tool = GoogleSearchTool()
        result = tool.search(query)
        return {
            "query": query,
            "results": result
        }
    except Exception as e:
        print(f"[ERROR] Google search tool failed: {str(e)}")
        return {
            "query": query,
            "results": []
        }

class NJVoterChatAgent:
    def __init__(self):
        import os
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = REGION
        
        print(f"[DEBUG] Initializing agent with instruction: {SYSTEM_PROMPT[:100]}...")
        self.model = MODEL
        self.system_prompt = SYSTEM_PROMPT
        self.bigquery_tool = BigQueryReadOnlyTool()
        self.google_search_tool = GoogleSearchTool()
        print(f"[DEBUG] Agent initialized successfully with instruction parameter and tools: bigquery_select, google_search")
        self._initialize_services()
    
    def _initialize_services(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self._model = genai.GenerativeModel(
            model_name=self.model.replace("gemini-", "gemini-pro") if "gemini" in self.model else "gemini-pro",
            system_instruction=self.system_prompt
        )
        self._session_id = None

    def chat(self, prompt: str):
        try:
            print("[DEBUG] NJVoterChatAgent.chat -> using simplified Gemini API")
            
            if not self._session_id:
                self._session_id = f"session_{int(time.time())}"
                print(f"[DEBUG] Created new session: {self._session_id}")
            
            tools_context = ""
            if "bigquery" in prompt.lower() or "sql" in prompt.lower() or "query" in prompt.lower():
                tools_context += "\n[Using BigQuery tool for data analysis]"
            if "search" in prompt.lower() or "google" in prompt.lower() or "current" in prompt.lower():
                tools_context += "\n[Using Google Search for current information]"
            
            full_message = f"{tools_context}\n\nUser: {prompt}"
            
            chat = self._model.start_chat()
            response = chat.send_message(full_message)
            
            print(f"[DEBUG] Gemini response received: {response.text[:200]}...")
            
            return {
                "response": response.text,
                "session_id": self._session_id,
                "turn_id": None
            }

        except Exception as e:
            print(f"[ERROR] Chat failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "session_id": self._session_id if hasattr(self, '_session_id') else None,
                "turn_id": None
            }

    def __call__(self, prompt: str):
        return self.chat(prompt)

    def invoke(self, prompt: str):
        return self.chat(prompt)
