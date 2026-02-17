from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def call_add_tool():

    async with streamablehttp_client(
        "http://localhost:8000"
    ) as (read, write, _):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                "add",
                {"a": 5, "b": 10}
            )

            return result
