# Step-by-Step MCP (FastMCP)

A **FastMCP** server with **MCP registry** entry and an **MCP connector** so remotely hosted agents can discover and use the server's tools over HTTP.

## Structure

- **`server/mcp_server.py`** — FastMCP server (tools + resources), runs over HTTP.
- **`registry/server.json`** — MCP registry entry (metadata + remote URL) for discovery.
- **`connector/mcp_connector.py`** — Connector so remote agents can list/call tools and read resources.

## Quick start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run the MCP server

```bash
python server/mcp_server.py
```

Server listens on `http://0.0.0.0:8000`; MCP endpoint is `http://localhost:8000/mcp`.

### 3. Use the connector (remote agent)

From the same machine or another host (if the server is reachable):

```bash
# List tools
python -m connector.mcp_connector list-tools

# Call a tool (args as JSON)
python -m connector.mcp_connector call add '{"a": 5, "b": 3}'
python -m connector.mcp_connector call greet '{"name": "Alice", "title": "Dr"}'

# List resources
python -m connector.mcp_connector list-resources

# Read a resource
python -m connector.mcp_connector read-resource resource://server/info
```

**Override server URL** (e.g. for a remotely hosted server):

```bash
set MCP_SERVER_URL=http://your-server:8000
python -m connector.mcp_connector list-tools
```

On Linux/macOS: `export MCP_SERVER_URL=http://your-server:8000`

If `MCP_SERVER_URL` is not set, the connector uses the URL from `registry/server.json` (default `http://localhost:8000/mcp`).

## MCP registry (`registry/server.json`)

The registry JSON describes the server for discovery:

- **name**: `com.example.step-by-step-mcp`
- **capabilities**: tools, resources
- **deployments**: remote entry with URL and `streamable-http` transport

When you deploy the server to a public or internal host, update the `url` in `registry/server.json` under `deployments[0]` so agents use the correct endpoint.

## Server tools

| Tool    | Description                    |
|---------|--------------------------------|
| `add`   | Add two integers.              |
| `greet` | Greeting with optional title.  |
| `echo`  | Echo a message (optional repeat). |

## Remote agent integration

A remotely hosted agent can:

1. **Discover**: Read `registry/server.json` (or your own registry) to get the server URL.
2. **Connect**: Use the connector or any MCP client that supports Streamable HTTP with that URL.
3. **Use tools**: Call `list-tools`, then `call <name> <json_args>` (or the client’s equivalent).

Example in Python (agent-side):

```python
from fastmcp import Client

client = Client("http://your-mcp-server:8000/mcp")
async with client:
    tools = await client.list_tools()
    result = await client.call_tool("add", {"a": 10, "b": 20})
```

## License

Use as you like; adjust names and registry content for your environment.
