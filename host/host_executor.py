"""
Host agent executor: reads agent_registry + agent_discovery and routes requests to registered agents.
"""
import sys
import uuid
from pathlib import Path

# Allow importing from project root (agent_discovery, agent_registry)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from a2a.client import A2AClient
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    MessageSendParams,
    SendMessageRequest,
)

import agent_discovery
from agent_discovery import resolve_agent_for_request


def _registry_to_agent_card(agent_config: dict) -> AgentCard:
    """Build A2A AgentCard from agent_registry.json entry."""
    skills = []
    for s in agent_config.get("skills", []):
        skills.append(
            AgentSkill(
                id=s.get("id", ""),
                name=s.get("name", ""),
                description=s.get("description", ""),
                tags=s.get("tags", []),
                examples=s.get("examples", []),
            )
        )
    return AgentCard(
        name=agent_config.get("name", "Agent"),
        description=agent_config.get("description", ""),
        url=agent_config.get("url", ""),
        version=agent_config.get("version", "1.0.0"),
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=skills or [AgentSkill(id="default", name="Default", description="", tags=[], examples=[])],
    )


class HostAgentExecutor(AgentExecutor):
    """Routes A2A requests to agents discovered from agent_registry.json."""

    def __init__(self, registry_path: str | Path | None = None):
        self._registry_path = registry_path
        self._clients: dict[str, A2AClient] = {}

    def _get_client(self, agent_config: dict) -> A2AClient:
        agent_id = agent_config.get("id", "")
        if agent_id not in self._clients:
            card = _registry_to_agent_card(agent_config)
            url = agent_config.get("url", "")
            httpx_client = httpx.AsyncClient(timeout=60.0)
            self._clients[agent_id] = A2AClient(httpx_client, card, url=url)
        return self._clients[agent_id]

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        agent_id = context.metadata.get("agent_id") if context.metadata else None
        skill_tag = context.metadata.get("skill_tag") if context.metadata else None
        user_message = context.get_user_input() if hasattr(context, "get_user_input") else None

        agent_config = resolve_agent_for_request(
            agent_id=agent_id,
            skill_tag=skill_tag,
            user_message=user_message,
            registry_path=self._registry_path,
        )
        if not agent_config:
            from a2a.utils.message import new_agent_text_message
            await event_queue.enqueue_event(
                new_agent_text_message("No agent available in registry.")
            )
            return

        client = self._get_client(agent_config)
        # Forward a new user message without host task/context ids so the backend creates a new task
        inbound = context.message
        forward_message = Message(
            kind="message",
            messageId=inbound.message_id or str(uuid.uuid4()),
            role=inbound.role,
            parts=inbound.parts,
            taskId=None,
            contextId=None,
            referenceTaskIds=None,
            extensions=inbound.extensions,
            metadata=inbound.metadata,
        )
        params = MessageSendParams(
            message=forward_message,
            configuration=None,
            metadata=context.metadata,
        )
        request = SendMessageRequest(id="host-1", method="message/send", params=params)

        try:
            response = await client.send_message(request)
            root = response.root
            if hasattr(root, "result"):
                await event_queue.enqueue_event(root.result)
            else:
                from a2a.utils.message import new_agent_text_message
                await event_queue.enqueue_event(
                    new_agent_text_message(f"Agent error: {getattr(root, 'message', root)}")
                )
        except Exception as e:
            from a2a.utils.message import new_agent_text_message
            await event_queue.enqueue_event(
                new_agent_text_message(f"Host routing error: {e!s}")
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError("Cancel not supported")
