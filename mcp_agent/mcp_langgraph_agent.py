"""
LangGraph agent that uses MCP server tools (via mcp_connector).
Connects to the server from mcp_registry, lists tools, and runs a ReAct agent with those tools.
"""
import os
import sys
from pathlib import Path
from typing import Any

# Project root for mcp_connector
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field, create_model

from mcp_connector import call_tool, create_client, get_server_url, list_tools

# Fallback input schemas for known MCP tools when the server does not return inputSchema.
# Ensures add, greet, echo always have correct required/optional params.
FALLBACK_INPUT_SCHEMAS: dict[str, dict] = {
    "add": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"},
        },
        "required": ["a", "b"],
    },
    "just_fun_random": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"},
        },
        "required": ["a", "b"],
    },
    "greet": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the person to greet"},
        },
        "required": ["name"],
    },
    "echo": {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Text to echo back"},
            "repeat": {"type": "integer", "description": "Number of times to repeat the message (optional, default 1)"},
        },
        "required": ["message"],
    },
}


def _content_to_str(content) -> str:
    """Turn MCP call_tool result content into a string for the agent."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if "text" in block:
                    parts.append(block["text"])
                else:
                    parts.append(str(block))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(content)


def _json_schema_type_to_python(prop_schema: dict) -> type:
    """Map JSON Schema type to Python type for Pydantic."""
    t = prop_schema.get("type", "string")
    if t == "string":
        return str
    if t == "integer":
        return int
    if t == "number":
        return float
    if t == "boolean":
        return bool
    if t == "array":
        return list
    if t == "object":
        return dict
    return str


def _input_schema_to_pydantic(tool_name: str, input_schema: dict) -> type[BaseModel] | None:
    """
    Build a Pydantic BaseModel from MCP tool input_schema (JSON Schema)
    so the LLM gets required/optional parameters (e.g. name for greet).
    """
    if not input_schema or not isinstance(input_schema, dict):
        return None
    properties = input_schema.get("properties") or {}
    required = set(input_schema.get("required") or [])
    if not properties:
        return None
    fields: dict[str, Any] = {}
    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            continue
        py_type = _json_schema_type_to_python(prop_schema)
        desc = prop_schema.get("description") or prop_name
        if prop_name in required:
            fields[prop_name] = (py_type, Field(description=desc))
        else:
            fields[prop_name] = (py_type | None, Field(default=None, description=desc))
    if not fields:
        return None
    model_name = f"{tool_name.replace('-', '_').title()}Input"
    return create_model(model_name, **fields)


def _get_effective_schema(tool_name: str, input_schema: dict | None) -> dict:
    """Use tool input_schema from MCP server, or fallback for known tools (add, greet, echo)."""
    if input_schema and isinstance(input_schema, dict) and input_schema.get("properties"):
        return input_schema
    return FALLBACK_INPUT_SCHEMAS.get(tool_name, {})


def _make_mcp_tool(client, name: str, description: str, input_schema: dict | None = None):
    """Build one LangChain tool that calls the MCP server for a given tool name."""
    effective_schema = _get_effective_schema(name, input_schema)
    args_schema = _input_schema_to_pydantic(name, effective_schema)

    async def _invoke(**kwargs) -> str:
        # Omit None values so optional params use server defaults (e.g. echo repeat)
        args = {k: v for k, v in kwargs.items() if v is not None}
        result = await call_tool(client, name, args)
        if result.get("isError"):
            return f"Error: {_content_to_str(result.get('content', result))}"
        return _content_to_str(result.get("content"))

    kwargs: dict[str, Any] = dict(
        coroutine=_invoke,
        name=name,
        description=description,
    )
    if args_schema is not None:
        kwargs["args_schema"] = args_schema
    return StructuredTool.from_function(**kwargs)


def _build_langchain_tools(client, mcp_tools_list: list) -> list:
    """Build LangChain StructuredTools from MCP tool list; each calls the MCP server.
    Uses server input_schema when present, else FALLBACK_INPUT_SCHEMAS for add/greet/echo.
    """
    return [
        _make_mcp_tool(
            client,
            t.get("name", ""),
            t.get("description") or f"Call MCP tool {t.get('name', '')}",
            t.get("input_schema"),
        )
        for t in mcp_tools_list
        if t.get("name")
    ]


async def run_mcp_agent(user_message: str, registry_path: str | Path | None = None) -> str:
    """
    Run the LangGraph agent with MCP tools. Uses mcp_registry to get server URL,
    connects, lists tools, and runs the agent. Returns the final text response.
    """
    url = get_server_url(registry_path)
    client = create_client(url=url, registry_path=registry_path)

    async with client:
        mcp_tools_list = await list_tools(client)
        if not mcp_tools_list:
            return "No tools available from the MCP server. Ask the operator to start the MCP server or check mcp_registry."

        lc_tools = _build_langchain_tools(client, mcp_tools_list)
        model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        agent = create_react_agent(
            model=model,
            tools=lc_tools,
            prompt=(
                "You are a helpful assistant with access to tools from an MCP server (add, greet, echo, etc.). "
                "Use the tools when they help answer the user. Reply concisely."
            ),
        )
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": user_message}],
        })
        messages = result.get("messages", [])
        if not messages:
            return "No response generated."
        last = messages[-1]
        if hasattr(last, "content"):
            return (last.content or "").strip() or "No response generated."
        if isinstance(last, dict):
            return (last.get("content") or "").strip() or "No response generated."
        return str(last).strip() or "No response generated."
