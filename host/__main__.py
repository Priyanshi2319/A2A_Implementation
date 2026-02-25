"""
Run the host A2A server: reads agent_registry.json and agent_discovery, routes requests to registered agents.
Reads mcp_registry and uses mcp_connector to list MCP tools for discovery. Default port 8080.
"""
import asyncio
import os
import sys
from pathlib import Path

# Project root for agent_discovery, agent_registry, mcp_registry, mcp_connector
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

import agent_discovery
from host.host_executor import HostAgentExecutor

MCP_REGISTRY_DIR = ROOT / "mcp_registry"


def main(host: str = "0.0.0.0", port: int = 8080, registry_path: str | Path | None = None):
    path = registry_path or ROOT / "agent_registry.json"
    agents = agent_discovery.get_agents(path)
    if not agents:
        raise ValueError("No agents in registry; ensure agent_registry.json has at least one enabled agent.")

    # Aggregate skills from all agents for the host card
    all_skills = []
    seen = set()
    for a in agents:
        for s in a.get("skills", []):
            sid = s.get("id", "")
            if sid and sid not in seen:
                seen.add(sid)
                all_skills.append(
                    AgentSkill(
                        id=sid,
                        name=s.get("name", ""),
                        description=s.get("description", ""),
                        tags=s.get("tags", []),
                        examples=s.get("examples", []),
                    )
                )

    # Read mcp_registry and use mcp_connector to list tools (for host card discovery)
    try:
        from mcp_connector import list_tools_from_registry
        mcp_tools = asyncio.run(list_tools_from_registry(MCP_REGISTRY_DIR))
        if mcp_tools:
            tool_names = [t.get("name", "") for t in mcp_tools if t.get("name")]
            if tool_names:
                all_skills.append(
                    AgentSkill(
                        id="mcp_registry_tools",
                        name="MCP registry tools",
                        description=f"Tools from mcp_registry (via mcp_connector): {', '.join(tool_names)}",
                        tags=["mcp", "tools", "registry"],
                        examples=[f"Use {n}" for n in tool_names[:3]],
                    )
                )
    except Exception:
        pass  # MCP server may be down; host still works

    if not all_skills:
        all_skills = [
            AgentSkill(id="default", name="Default", description="Route to registered agents", tags=[], examples=[])
        ]

    app_url = os.environ.get("HOST_URL", f"http://{host}:{port}")
    agent_card = AgentCard(
        name="A2A Host Agent",
        description="Routes requests to agents in agent_registry. Uses mcp_registry and mcp_connector to provide MCP tools via the MCP Tool Agent.",
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=all_skills,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=HostAgentExecutor(registry_path=path),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    main()
