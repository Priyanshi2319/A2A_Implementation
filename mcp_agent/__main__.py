"""
Run the MCP-backed A2A agent (reads mcp_registry, uses mcp_connector for tools).
Default port 8002. Set OPENAI_API_KEY. MCP server URL from mcp_registry/server.json or MCP_SERVER_URL.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
load_dotenv()

from mcp_agent.mcp_agent_executor import MCPAgentExecutor

MCP_REGISTRY = ROOT / "mcp_registry"


def main(host: str = "0.0.0.0", port: int = 8002, registry_path: str | Path | None = None):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")

    path = registry_path or MCP_REGISTRY
    skill = AgentSkill(
        id="mcp_tools",
        name="MCP tools",
        description="Use remote MCP server tools (add, greet, echo,just_fun_random etc.) to answer questions",
        tags=["mcp", "tools", "assistant"],
        examples=["Add 3 and 5", "Greet Alice", "Echo hello world" , "generate random number"],
    )

    app_url = os.environ.get("MCP_AGENT_URL", f"http://{host}:{port}")
    agent_card = AgentCard(
        name="MCP Tool Agent",
        description="LangGraph agent that uses tools from the MCP server (mcp_registry).",
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=MCPAgentExecutor(registry_path=path),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    main()
