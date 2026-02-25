"""
Run the LangGraph A2A agent server (OpenAI).
Set OPENAI_API_KEY in env. Default port 8001.
"""
import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
load_dotenv()
from agent.agent_executor import LangGraphAgentExecutor


def main(host: str = "0.0.0.0", port: int = 8001):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")

    skill = AgentSkill(
        id="general_assistant",
        name="General Assistant",
        description="Answers questions and assists with general tasks using OpenAI",
        tags=["assistant", "openai", "langgraph"],
        examples=["What is the capital of France?", "Explain recursion briefly"],
    )

    app_url = os.environ.get("AGENT_URL", f"http://{host}:{port}")
    agent_card = AgentCard(
        name="LangGraph Assistant",
        description="A simple LangGraph agent powered by OpenAI.",
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    main()
