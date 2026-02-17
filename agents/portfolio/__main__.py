# Your custom A2A server class
from server.server import A2AServer

# Models for describing agent capabilities and metadata
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# Task manager and agent logic
from agents.portfolio.task_manager import AgentTaskManager
from agents.portfolio.agent import PortfolioAgent

# CLI and logging support
import click           # For creating a clean command-line interface
import logging         # For logging errors and info to the console


# -----------------------------------------------------------------------------
# Setup logging to print info to the console
# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Main Entry Function – Configurable via CLI
# -----------------------------------------------------------------------------

@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=9001, help="Port number for the server")
def main(host, port):
    """
    This function sets up everything needed to start the agent server.
    You can run it via: `python -m agents.google_adk --host 0.0.0.0 --port 12345`
    """

    # Define what this agent can do – in this case, it does NOT support streaming
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers (used in directories and UIs)
    skill = AgentSkill(
        id="portfolio",                                 # Unique skill ID
        name="Portfolio accounts Tool",                          # Human-friendly name
        description="Replies with the Portfolio accounts lists",    # What the skill does
        tags=["portfolio accounts list"],                                  # Optional tags for searching
        examples=["give me list of portfolio accounts", "portfolio account lists","tell me portfolio accounts"]  # Example queries
    )

    # Create an agent card describing this agent’s identity and metadata
    agent_card = AgentCard(
        name="PortfolioAgent",                               # Name of the agent
        description="This agent Replies with the Portfolio accounts lists.",  # Description
        url=f"http://{host}:{port}/",                       # The public URL where this agent lives
        version="1.0.0",                                    # Version number
        defaultInputModes=PortfolioAgent.SUPPORTED_CONTENT_TYPES,  # Input types this agent supports
        defaultOutputModes=PortfolioAgent.SUPPORTED_CONTENT_TYPES, # Output types it produces
        capabilities=capabilities,                          # Supported features (e.g., streaming)
        skills=[skill]                                      # List of skills it supports
    )

    # Start the A2A server with:
    # - the given host/port
    # - this agent’s metadata
    # - a task manager that runs the PortfolioAgent
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=AgentTaskManager(agent=PortfolioAgent())
    )

    # Start listening for tasks
    server.start()


# -----------------------------------------------------------------------------
# This runs only when executing the script directly via `python -m`
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
