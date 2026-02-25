"""
Agent discovery module: loads agent_registry.json and provides lookup/routing helpers.
"""
import json
import os
from pathlib import Path
from typing import Any

# Default path to registry relative to this file
DEFAULT_REGISTRY_PATH = Path(__file__).parent / "agent_registry.json"


def load_registry(registry_path: str | Path | None = None) -> dict[str, Any]:
    """Load agent registry from JSON file."""
    path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
    if not path.is_file():
        return {"agents": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_agents(registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return list of all registered agents (enabled only by default)."""
    registry = load_registry(registry_path)
    agents = registry.get("agents", [])
    return [a for a in agents if a.get("enabled", True)]


def get_agent_by_id(
    agent_id: str,
    registry_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return agent config by id or None if not found."""
    for agent in get_agents(registry_path):
        if agent.get("id") == agent_id:
            return agent
    return None


def get_agent_url(agent_id: str, registry_path: str | Path | None = None) -> str | None:
    """Return agent base URL by id or None."""
    agent = get_agent_by_id(agent_id, registry_path)
    return agent.get("url") if agent else None


def list_agent_ids(registry_path: str | Path | None = None) -> list[str]:
    """Return list of enabled agent ids."""
    return [a["id"] for a in get_agents(registry_path) if a.get("id")]


# Keywords that suggest the user wants MCP tools (greet, add, echo). Used for content-based routing.
MCP_TOOL_ROUTING_KEYWORDS = ("greet", "add", "echo", "sum", "hello " , "random generator")


def resolve_agent_for_request(
    agent_id: str | None = None,
    skill_tag: str | None = None,
    user_message: str | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """
    Resolve which agent should handle a request.
    - If agent_id is given, return that agent.
    - If skill_tag is given, return first agent that has a skill with matching tag.
    - If user_message suggests MCP tool use (e.g. "greet", "add", "echo"), return MCP Tool Agent.
    - Otherwise return first enabled agent (default).
    """
    agents = get_agents(registry_path)
    if not agents:
        return None
    if agent_id:
        return get_agent_by_id(agent_id, registry_path)
    if skill_tag:
        for agent in agents:
            for skill in agent.get("skills", []):
                if skill_tag in skill.get("tags", []):
                    return agent
    # Content-based: route to MCP Tool Agent when message suggests tool use
    if user_message:
        msg_lower = user_message.strip().lower()
        if any(kw in msg_lower for kw in MCP_TOOL_ROUTING_KEYWORDS):
            mcp_agent = get_agent_by_id("mcp-tool-agent", registry_path)
            if mcp_agent:
                return mcp_agent
    return agents[0]
