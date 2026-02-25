"""
MCP Connector for remote agents.

Connects to a remotely hosted MCP server (via URL from mcp_registry or env),
lists tools/resources, and calls tools so a remote agent can use the server.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Default: mcp_registry/server.json next to the project root (parent of mcp_connector)
MCP_REGISTRY_DIR = Path(__file__).resolve().parent.parent / "mcp_registry"
DEFAULT_REGISTRY_FILE = MCP_REGISTRY_DIR / "server.json"


def load_registry(registry_path: str | Path | None = None) -> dict:
    """Load MCP server registry from JSON (file or dir/server.json)."""
    path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_FILE
    if path.is_dir():
        path = path / "server.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_server_url(registry_path: str | Path | None = None) -> str:
    """Server URL: MCP_SERVER_URL env, or from mcp_registry server.json."""
    url = os.environ.get("MCP_SERVER_URL", "").strip()
    if url:
        return url.rstrip("/") if url.endswith("/") else url
    data = load_registry(registry_path)
    deployments = data.get("deployments") or []
    for d in deployments:
        if d.get("kind") == "remote" and d.get("url"):
            return d["url"].rstrip("/")
    return "http://localhost:8092/mcp"


def _get_server_url() -> str:
    """Backward-compat: same as get_server_url()."""
    return get_server_url()


def _normalize_input_schema(schema: Any) -> dict:
    """Ensure input_schema is a dict (MCP may return object or dict)."""
    if schema is None:
        return {}
    if isinstance(schema, dict):
        return schema
    if hasattr(schema, "model_dump"):
        return schema.model_dump()
    if hasattr(schema, "dict"):
        return schema.dict()
    return {}


async def list_tools(client) -> list:
    """List tools exposed by the MCP server."""
    tools = await client.list_tools()
    return [
        {
            "name": t.name,
            "description": (t.description or ""),
            "input_schema": _normalize_input_schema(getattr(t, "inputSchema", None) or getattr(t, "input_schema", None)),
        }
        for t in tools
    ]


async def list_tools_from_registry(registry_path: str | Path | None = None) -> list:
    """
    Connect to the MCP server from mcp_registry, list tools, and return them.
    Returns [] if the server is unavailable or on error.
    """
    try:
        client = create_client(registry_path=registry_path)
        async with client:
            return await list_tools(client)
    except Exception:
        return []


async def list_resources(client) -> list:
    """List resources exposed by the MCP server."""
    resources = await client.list_resources()
    return [{"uri": r.uri, "name": getattr(r, "name", r.uri), "description": getattr(r, "description", "")} for r in resources]


async def call_tool(client, name: str, arguments: dict) -> dict:
    """Call a tool by name with the given arguments."""
    result = await client.call_tool(name, arguments)
    content = getattr(result, "content", result)
    is_error = getattr(result, "is_error", getattr(result, "isError", False))
    return {"content": content, "isError": is_error}


async def read_resource(client, uri: str) -> dict:
    """Read a resource by URI."""
    result = await client.read_resource(uri)
    return {"contents": result.contents if hasattr(result, "contents") else result, "uri": uri}


def create_client(url: str | None = None, registry_path: str | Path | None = None):
    """Create an MCP Client for the given URL (or from registry). Caller must use async with client."""
    try:
        from fastmcp import Client
    except ImportError:
        raise ImportError("Install fastmcp: pip install fastmcp") from None
    url = url or get_server_url(registry_path)
    return Client(url)


async def run_connector(url: str, command: str, *args) -> None:
    """Run connector: list-tools | list-resources | call <name> <json_args> | read-resource <uri>."""
    try:
        from fastmcp import Client
    except ImportError:
        print("Install fastmcp: pip install fastmcp", file=sys.stderr)
        sys.exit(1)

    url = url or get_server_url()
    client = Client(url)

    async with client:
        if command == "list-tools":
            tools = await list_tools(client)
            print(json.dumps({"tools": tools}, indent=2))

        elif command == "list-resources":
            resources = await list_resources(client)
            print(json.dumps({"resources": resources}, indent=2))

        elif command == "call" and len(args) >= 1:
            name = args[0]
            raw_args = args[1] if len(args) > 1 else "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON arguments"}), file=sys.stderr)
                sys.exit(1)
            result = await call_tool(client, name, arguments)
            print(json.dumps(result, indent=2))

        elif command == "read-resource" and len(args) >= 1:
            uri = args[0]
            result = await read_resource(client, uri)
            print(json.dumps(result, indent=2))

        else:
            print(
                "Usage: mcp_connector list-tools | list-resources | call <tool_name> [json_args] | read-resource <uri>",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    url = get_server_url()
    argv = sys.argv[1:]
    if not argv:
        print(f"Server URL: {url}", file=sys.stderr)
        print("Usage: mcp_connector list-tools | list-resources | call <name> [json_args] | read-resource <uri>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run_connector(url, argv[0], *argv[1:]))


if __name__ == "__main__":
    main()
