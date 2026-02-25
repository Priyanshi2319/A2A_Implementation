"""
LangGraph agent executor: bridges A2A protocol and the LangGraph OpenAI agent.
"""
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message

from agent.langgraph_agent import run_agent  # noqa: E402


class LangGraphAgentExecutor(AgentExecutor):
    """A2A AgentExecutor that runs the LangGraph OpenAI agent."""

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
            result = await run_agent(user_input.strip())
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
