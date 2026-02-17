# =============================================================================
# agents/google_adk/agent.py
# =============================================================================
# 🎯 Purpose:
# This file defines a very simple AI agent called PortfolioAgent.
# It uses Google's ADK (Agent Development Kit) and Gemini model to respond with the current time.
# =============================================================================


# -----------------------------------------------------------------------------
# 📦 Built-in & External Library Imports
# -----------------------------------------------------------------------------

from datetime import datetime
import traceback  # Used to get the current system time

# 🧠 Gemini-based AI agent provided by Google's ADK
from google.adk.agents.llm_agent import LlmAgent

# 📚 ADK services for session, memory, and file-like "artifacts"
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

# 🏃 The "Runner" connects the agent, session, memory, and files into a complete system
from google.adk.runners import Runner

# 🧾 Gemini-compatible types for formatting input/output messages
from google.genai import types
from agents.portfolio.mcp_client import call_add_tool

import asyncio
# 🔐 Load environment variables (like API keys) from a `.env` file
from dotenv import load_dotenv
load_dotenv()  # Load variables like GOOGLE_API_KEY into the system
# This allows you to keep sensitive data out of your code.


# -----------------------------------------------------------------------------
# 🕒 PortfolioAgent: Your AI agent that tells the time
# -----------------------------------------------------------------------------

class PortfolioAgent:
    # This agent only supports plain text input/output
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    # def __init__(self):
    #     """
    #     👷 Initialize the PortfolioAgent:
    #     - Creates the LLM agent (powered by Gemini)
    #     - Sets up session handling, memory, and a runner to execute tasks
    #     """
    #     #self._agent = self._build_agent()  # Set up the Gemini agent
    #     self._user_id = "portfolio_agent_user"  # Use a fixed user ID for simplicity

    #     # 🧠 The Runner is what actually manages the agent and its environment
    #     self._runner = Runner(
    #         app_name=self._agent.name,
    #         agent=self._agent,
    #         artifact_service=InMemoryArtifactService(),  # For files (not used here)
    #         session_service=InMemorySessionService(),    # Keeps track of conversations
    #         memory_service=InMemoryMemoryService(),      # Optional: remembers past messages
    #     )

    # def _build_agent(self) -> LlmAgent:
    #     """
    #     ⚙️ Creates and returns a Gemini agent with basic settings.

    #     Returns:
    #         LlmAgent: An agent object from Google's ADK
    #     """
    #     return LlmAgent(
    #         model="gemini-2.5-flash",         # Gemini model version
    #         name="portfolio_agent",                  # Name of the agent
    #         description="Tell me the portfolio status",    # Description for metadata
    #         instruction="Reply with the List of tables"  # System prompt
    #     )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        📥 Handle a user query and return a response string.
        Note - function updated 28 May 2025
        Summary of changes:
        1. Agent's invoke method is made async
        2. All async calls (get_session, create_session, run_async) 
            are awaited inside invoke method
        3. task manager's on_send_task updated to await the invoke call

        Reason - get_session and create_session are async in the 
        "Current" Google ADK version and were synchronous earlier 
        when this lecture was recorded. This is due to a recent change 
        in the Google ADK code 
        https://github.com/google/adk-python/commit/1804ca39a678433293158ec066d44c30eeb8e23b

        Args:
            query (str): What the user said (e.g., "what time is it?")
            session_id (str): Helps group messages into a session

        Returns:
            str: Agent's reply (usually the current time)
        """
        try:

            # # 🔁 Try to reuse an existing session (or create one if needed)
            # session = await self._runner.session_service.get_session(
            #     app_name=self._agent.name,
            #     user_id=self._user_id,
            #     session_id=session_id
            # )

            # if session is None:
            #     session = await self._runner.session_service.create_session(
            #         app_name=self._agent.name,
            #         user_id=self._user_id,
            #         session_id=session_id,
            #         state={}  # Optional dictionary to hold session state
            #     )

            # # 📨 Format the user message in a way the Gemini model expects
            # content = types.Content(
            #     role="user",
            #     parts=[types.Part.from_text(text=query)]
            # )

            # 🚀 Run the agent using the Runner and collect the last event
            # last_event = None
            # async for event in self._runner.run_async(
            #     user_id=self._user_id,
            #     session_id=session.id,
            #     new_message=content
            # ):
            #     last_event = event

            # # 🧹 Fallback: return empty string if something went wrong
            # if not last_event or not last_event.content or not last_event.content.parts:
            #     return ""

            # 📤 Extract and join all text responses into one string
            #return "\n".join([p.text for p in last_event.content.parts if p.text])

            # result = result = await call_add_tool()


            # return {"result": result}
            return "[{\"account_id\":\"PF-1001\",\"account_name\":\"Alpha Growth Fund\",\"portfolio_type\":\"Equity\",\"region\":\"US\",\"aum_usd\":12500000,\"risk_profile\":\"High\",\"status\":\"Active\"},{\"account_id\":\"PF-1002\",\"account_name\":\"Secure Income Portfolio\",\"portfolio_type\":\"Fixed Income\",\"region\":\"Europe\",\"aum_usd\":8200000,\"risk_profile\":\"Low\",\"status\":\"Active\"},{\"account_id\":\"PF-1003\",\"account_name\":\"Balanced Opportunity Fund\",\"portfolio_type\":\"Hybrid\",\"region\":\"APAC\",\"aum_usd\":6750000,\"risk_profile\":\"Medium\",\"status\":\"Active\"},{\"account_id\":\"PF-1004\",\"account_name\":\"Tech Innovation Portfolio\",\"portfolio_type\":\"Equity\",\"region\":\"US\",\"aum_usd\":15300000,\"risk_profile\":\"High\",\"status\":\"Active\"},{\"account_id\":\"PF-1005\",\"account_name\":\"Global Dividend Fund\",\"portfolio_type\":\"Equity\",\"region\":\"Global\",\"aum_usd\":9400000,\"risk_profile\":\"Medium\",\"status\":\"Active\"},{\"account_id\":\"PF-1006\",\"account_name\":\"Capital Preservation Fund\",\"portfolio_type\":\"Debt\",\"region\":\"Europe\",\"aum_usd\":5600000,\"risk_profile\":\"Low\",\"status\":\"Active\"},{\"account_id\":\"PF-1007\",\"account_name\":\"Emerging Markets Alpha\",\"portfolio_type\":\"Equity\",\"region\":\"APAC\",\"aum_usd\":7950000,\"risk_profile\":\"High\",\"status\":\"Under Review\"},{\"account_id\":\"PF-1008\",\"account_name\":\"ESG Sustainable Portfolio\",\"portfolio_type\":\"Thematic\",\"region\":\"Global\",\"aum_usd\":11200000,\"risk_profile\":\"Medium\",\"status\":\"Active\"},{\"account_id\":\"PF-1009\",\"account_name\":\"Real Asset Allocation Fund\",\"portfolio_type\":\"Alternative\",\"region\":\"US\",\"aum_usd\":13800000,\"risk_profile\":\"Medium\",\"status\":\"Active\"},{\"account_id\":\"PF-1010\",\"account_name\":\"Short-Term Liquidity Fund\",\"portfolio_type\":\"Money Market\",\"region\":\"Global\",\"aum_usd\":4300000,\"risk_profile\":\"Low\",\"status\":\"Active\"}]"

        except Exception as e:
            # Print a user-friendly error message
            print(f"🔥🔥🔥 An error occurred in PortfolioAgent.invoke: {e}")

            # Print the full, detailed stack trace to the console
            traceback.print_exc()

            # Return a helpful error message to the user/client
            return "Sorry, I encountered an internal error and couldn't process your request."
