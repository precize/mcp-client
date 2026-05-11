import logging
import os
import json
import yaml
from pathlib import Path
from dotenv import load_dotenv # type: ignore

import vertexai # type: ignore
from google.adk.agents import Agent # type: ignore
from google.adk.tools.mcp_tool import McpToolset # type: ignore
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams # type: ignore
from vertexai.agent_engines import AdkApp # type: ignore

load_dotenv()

# Use Vertex AI backend instead of Gemini API
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

def load_yaml_config(key_path, default=None):
    """Generic method to load values from config.yaml

    Args:
        key_path: dot-separated path (e.g., "spec.agent.model")
        default: default value if not found

    Returns:
        Value from YAML or default
    """
    config_paths = [
        Path(__file__).parent / "config.yaml",  # Runtime config (deployed with code)
        Path(__file__).parent.parent / ".adk" / "config.yaml",  # Local dev config
        Path(".adk/config.yaml"),  # Fallback
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                # Navigate through nested keys
                value = config
                for key in key_path.split("."):
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                if value is not None:
                    return value
            except Exception as e:
                pass

    return default


def load_required_yaml_config(key_path):
    value = load_yaml_config(key_path)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing required config value: {key_path}")
    return value


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add file handler to write directly to app.log
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load all configuration from YAML
project = load_required_yaml_config("spec.projectId")
region = load_required_yaml_config("spec.region")
MODEL = load_required_yaml_config("spec.agent.model")
MODEL_LOCATION = load_required_yaml_config("spec.agent.region")

os.environ["GOOGLE_CLOUD_PROJECT"] = project
os.environ["GOOGLE_CLOUD_LOCATION"] = MODEL_LOCATION

logger.info(
    "Configuration - Project: %s, Agent Engine region: %s, Model location: %s, Model: %s",
    project,
    region,
    MODEL_LOCATION,
    MODEL,
)

# Initialize Vertex AI for Gemini model calls.
vertexai.init(project=project, location=MODEL_LOCATION)


def load_mcp_servers_from_config():
    """Load MCP server configurations from JSON file."""
    config_path = Path(__file__).parent / "mcp-config.json"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return []

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        servers = []
        for server_config in config.get("servers", []):
            if server_config.get("enabled", True):
                servers.append({
                    "name": server_config["name"],
                    "url": server_config["url"],
                    "auth_token": server_config["auth_token"],
                    "timeout": server_config.get("timeout", 180),
                    "retry_count": server_config.get("retry_count", 3),
                    "tool_filter": [],
                })
                logger.info(f"✓ Loaded MCP server: {server_config['name']}")
            else:
                logger.info(f"⊘ Skipped disabled MCP server: {server_config['name']}")

        logger.info(f"Total enabled MCP servers: {len(servers)}")
        return servers

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file: {e}")
        return []
    except KeyError as e:
        logger.error(f"Missing required field in config: {e}")
        return []


servers = load_mcp_servers_from_config()


def build_mcp_toolsets():
    """Build MCP toolsets for the agent."""
    toolsets = []

    # Skip during ADK deployment packaging to avoid connection timeouts
    if os.environ.get("ADK_DEPLOYMENT_SKIP_MCP") or os.environ.get("DEPLOYING_TO_VERTEX_AI"):
        logger.info("Skipping MCP toolset registration during deployment")
        return toolsets

    for server in servers:
        name = server["name"]
        url = server["url"]
        auth_token = server.get("auth_token", "")
        tool_filter = server.get("tool_filter", [])

        logger.info(f"Registering MCP toolset: {name} @ {url}")
        try:
            conn_params = StreamableHTTPConnectionParams(
                url=url,
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=180,
            )
            toolset = McpToolset(
                connection_params=conn_params,
                tool_filter=tool_filter if tool_filter else None,
            )
            toolsets.append(toolset)
            logger.info(f"Registered toolset: {name}")
        except Exception as e:
            logger.warning(f"Failed to register toolset '{name}': {e}")

    return toolsets


toolsets = build_mcp_toolsets()

root_agent = Agent(
    model=MODEL,
    name="generic_mcp_agent",
    instruction=(
        "You are a generic enterprise assistant. "
        "Use available MCP tools when they are relevant. "
        "If multiple tools are available, choose the most relevant one. "
        "Explain clearly what you are doing and summarize tool results."
    ),
    tools=toolsets,
)

app = AdkApp(agent=root_agent)

if __name__ == "__main__":
    logger.info("Agent Engine is ready for Vertex AI deployment")
    logger.info(f"Agent: {root_agent.name}")
    logger.info(f"Model: {root_agent.model}")
    logger.info(f"Tools: {len(root_agent.tools) if root_agent.tools else 0}")
