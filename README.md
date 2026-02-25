# LangGraph A2A Agent + Host

A simple **LangGraph** agent using the **a2a-sdk** and **OpenAI**, with an **agent registry** (JSON), **agent discovery** (Python), and a **host** that routes requests to registered agents.

## Layout

- **`agent_registry.json`** – Registry of agents (id, name, url, skills, enabled).
- **`agent_discovery.py`** – Loads the registry and provides `get_agents()`, `get_agent_by_id()`, `resolve_agent_for_request()`, etc.
- **`agent/`** – LangGraph + OpenAI agent exposed as an A2A server:
  - `langgraph_agent.py` – LangGraph `create_react_agent` with OpenAI (no tools).
  - `agent_executor.py` – A2A `AgentExecutor` that runs the LangGraph agent and pushes replies to the event queue.
  - `__main__.py` – Runs the A2A server (default port **8001**).
- **`host/`** – Host A2A server that reads the registry and discovery and routes requests:
  - `host_executor.py` – Executor that resolves which agent to call and forwards the request via `A2AClient`.
  - `__main__.py` – Runs the host server (default port **8080**); reads **mcp_registry** and uses **mcp_connector** to list MCP tools for discovery.
- **`mcp_registry/`** – MCP server registry (e.g. `server.json` with `deployments[].url` for the remote MCP server).
- **`mcp_connector/`** – Connects to the MCP server from the registry, lists tools/resources, and calls tools (`list_tools`, `call_tool`, `create_client`, `list_tools_from_registry`).
- **`mcp_agent/`** – LangGraph agent that uses the MCP server and its tools to reply:
  - `mcp_langgraph_agent.py` – Loads MCP URL from mcp_registry, connects via mcp_connector, builds LangChain tools from MCP tools, runs a ReAct agent.
  - `mcp_agent_executor.py` – A2A `AgentExecutor` that runs the MCP-backed agent.
  - `__main__.py` – Runs the MCP Tool Agent A2A server (default port **8002**).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Set **`OPENAI_API_KEY`** in the environment (required for the LangGraph agent).

## Run

1. **Start the LangGraph agent** (A2A server on port 8001):

   ```bash
   python -m agent
   ```

2. **Optional: start the MCP server** (e.g. the Step-by-Step MCP server on port 8092). The **MCP Tool Agent** and the **host** use **mcp_registry** and **mcp_connector** to connect to it.

3. **Optional: start the MCP Tool Agent** (A2A server on port 8002; uses MCP tools to reply):

   ```bash
   python -m mcp_agent
   ```

4. **Start the host** (reads `agent_registry.json` and mcp_registry, uses agent_discovery and mcp_connector to route and list tools):

   ```bash
   python -m host
   ```

5. **Call the host** (e.g. with an A2A client or curl). The host uses `agent_discovery` to resolve the agent (by default the first enabled agent in the registry) and forwards the request to it.

## Testing with JSON-RPC

A2A uses JSON-RPC 2.0. The server accepts **POST** at **`/`** with a JSON body.

**Sample request** (see `test_message_send.json`):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "kind": "message",
      "messageId": "test-msg-001",
      "role": "user",
      "parts": [
        { "kind": "text", "text": "What is 2 + 2? Reply in one sentence." }
      ]
    },
    "metadata": {}
  }
}
```

**Test the host** (agent must be running on 8001):

```bash
curl -X POST http://localhost:8080/ -H "Content-Type: application/json" -d @test_message_send.json
```

**Test the agent directly** (skip the host):

```bash
curl -X POST http://localhost:8001/ -H "Content-Type: application/json" -d @test_message_send.json
```

**Optional routing via host:** to target a specific agent or skill, add to `params.metadata`:

```json
"metadata": { "agent_id": "langgraph-assistant" }
```
```json
"metadata": { "agent_id": "mcp-tool-agent" }
```
or
```json
"metadata": { "skill_tag": "assistant" }
```

The response is JSON-RPC: either a **result** (e.g. `Message` with `role: "agent"` and `parts`) or an **error** object.

## Agent registry

`agent_registry.json` lists agents and their URLs. The host uses **agent_discovery** to:

- **List** enabled agents.
- **Resolve** which agent handles a request:
  - Optional **`metadata.agent_id`** – use that agent id.
  - Optional **`metadata.skill_tag`** – use first agent whose skill has that tag.
  - Otherwise use the **first enabled agent**.

Example:

```json
{
  "agents": [
    {
      "id": "langgraph-assistant",
      "name": "LangGraph Assistant",
      "url": "http://localhost:8001",
      "version": "1.0.0",
      "skills": [...],
      "enabled": true
    }
  ]
}
```

## MCP (mcp_registry + mcp_connector)

- **mcp_registry/server.json** – Describes the remote MCP server (e.g. `deployments[].url`: `http://localhost:8092/mcp`). Override with **`MCP_SERVER_URL`**.
- **mcp_connector** – `get_server_url()`, `create_client()`, `list_tools(client)`, `call_tool(client, name, arguments)`, `list_tools_from_registry(registry_path)` (async, used by the host to list tools at startup).
- The **host** reads mcp_registry and calls **list_tools_from_registry** at startup; if the MCP server is reachable, it adds an "MCP registry tools" skill to the host card with the tool names.
- The **MCP Tool Agent** (port 8002) connects to the MCP server from the registry, lists tools, and runs a LangGraph ReAct agent with those tools to answer user messages.

## Optional env

- **Agent:** `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`), `AGENT_URL` (for card URL).
- **MCP Agent:** `OPENAI_API_KEY`, `MCP_AGENT_URL`, `MCP_SERVER_URL` (or use mcp_registry).
- **Host:** `HOST_URL` (for card URL). Registry path is the project-root `agent_registry.json` unless you pass it in code.
