"""
A2A AgentExecutor for the MCP-backed LangGraph agent.
"""
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message

from mcp_agent.mcp_langgraph_agent import run_mcp_agent


class MCPAgentExecutor(AgentExecutor):
    """Executor that runs the MCP tool-backed LangGraph agent."""

    def __init__(self, registry_path: str | Path | None = None):
        self._registry_path = registry_path

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        if not user_input or not user_input.strip():
            await event_queue.enqueue_event(
                new_agent_text_message("Please provide a message.")
            )
            return
        try:
            result = await run_mcp_agent(
                user_input.strip(),
                registry_path=self._registry_path,
            )
            await event_queue.enqueue_event(new_agent_text_message(result))
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: {e!s}")
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError("Cancel not supported")
