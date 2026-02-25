"""
Simple LangGraph agent using OpenAI (no tools).
"""
import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def _get_agent():
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return create_react_agent(
        model=model,
        tools=[],  # No tools for simple agent
        prompt="You are a helpful assistant. Answer concisely.",
    )


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = _get_agent()
    return _agent


async def run_agent(user_message: str) -> str:
    """Run the LangGraph agent and return the final text response."""
    agent = get_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_message}]})
    messages = result.get("messages", [])
    if not messages:
        return "No response generated."
    last = messages[-1]
    if hasattr(last, "content"):
        return (last.content or "").strip() or "No response generated."
    if isinstance(last, dict):
        return (last.get("content") or "").strip() or "No response generated."
    return str(last).strip() or "No response generated."
