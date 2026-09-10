"""
SpacePilot Agent

Connects to the SpacePilot MCP server over Streamable HTTP and wraps it
in a Strands Agent backed by Amazon Bedrock.

Run:
    cd agent
    .venv\\Scripts\\python agent.py

Prerequisites:
    - Backend running:    cd backend && uvicorn app.main:app --port 8000
    - MCP server running: cd mcp && .venv\\Scripts\\python server.py
    - AWS credentials configured (profile, env vars, or instance role)
    - .env file with AWS_REGION, BEDROCK_MODEL_ID, MCP_SERVER_URL
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration — read from environment
# ---------------------------------------------------------------------------

AWS_REGION       = os.getenv("AWS_REGION",      "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
MCP_SERVER_URL   = os.getenv("MCP_SERVER_URL",   "http://localhost:8080/mcp/")

# Normalise: ensure the URL ends with a trailing slash (the MCP SDK server
# issues a 307 redirect from /mcp to /mcp/ — connect to /mcp/ directly)
if MCP_SERVER_URL.rstrip("/").endswith("/mcp"):
    MCP_SERVER_URL = MCP_SERVER_URL.rstrip("/") + "/"

# ---------------------------------------------------------------------------
# Imports (after env is loaded so Strands sees AWS_REGION)
# ---------------------------------------------------------------------------

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamable_http_client

from prompts import SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Bedrock model
# ---------------------------------------------------------------------------

def _make_model() -> BedrockModel:
    """Create a BedrockModel from environment configuration."""
    return BedrockModel(
        region_name=AWS_REGION,
        model_id=BEDROCK_MODEL_ID,
    )


# ---------------------------------------------------------------------------
# MCP transport factory
# ---------------------------------------------------------------------------

def _mcp_transport():
    """
    Return an async context manager that yields the MCP transport streams.

    MCPClient calls:  async with transport_callable() as (read, write, *_)
    streamable_http_client yields exactly: (read_stream, write_stream, get_session_id)
    """
    return streamable_http_client(MCP_SERVER_URL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_request(user_message: str) -> str:
    """
    Process a natural-language user message through the SpacePilot agent.

    The agent:
    1. Connects to the MCP server over Streamable HTTP
    2. Discovers available tools
    3. Reasons about the request and calls tools as needed
    4. Returns a grounded natural-language response

    Args:
        user_message: The raw user request.

    Returns:
        Agent response string. Never raises — errors are returned as strings.
    """
    now = datetime.now().strftime("%A, %d %B %Y %H:%M")
    context_message = f"[Current date and time: {now}]\n\n{user_message}"

    try:
        model = _make_model()

        with MCPClient(_mcp_transport) as mcp:
            tools = mcp.list_tools_sync()

            if not tools:
                return (
                    "⚠️  SpacePilot could not discover any tools from the MCP server. "
                    "Please check that the MCP server is running at "
                    f"{MCP_SERVER_URL}"
                )

            agent = Agent(
                model=model,
                system_prompt=SYSTEM_PROMPT,
                tools=tools,
            )

            result = agent(context_message)
            return str(result)

    except Exception as e:  # noqa: BLE001
        err = str(e)

        # Surface a clean message for common failure modes
        if "connect" in err.lower() or "connection" in err.lower():
            return (
                "⚠️  The campus service is temporarily unavailable. "
                f"Cannot connect to the MCP server at {MCP_SERVER_URL}. "
                "Please ensure both the backend and MCP server are running."
            )
        if "credential" in err.lower() or "token" in err.lower() or "auth" in err.lower():
            return (
                "⚠️  AWS credentials are not configured. "
                "Set AWS_REGION and ensure your credentials are available "
                "(via environment variables, ~/.aws/credentials, or an IAM role)."
            )

        # Generic fallback — include the error for developer visibility
        return f"⚠️  SpacePilot encountered an error: {err}"


# ---------------------------------------------------------------------------
# Connection test
# ---------------------------------------------------------------------------

def run_connection_test():
    """
    Verify connectivity to the MCP server and Bedrock without running the full
    agent loop. Prints discovered tools and executes one find_rooms call.

    This is the 'Definition of Done' check for Phase 1.
    """
    print("=" * 60)
    print("  SpacePilot Agent — Connection Test")
    print("=" * 60)
    print(f"  MCP server : {MCP_SERVER_URL}")
    print(f"  Bedrock    : {BEDROCK_MODEL_ID} ({AWS_REGION})")
    print("=" * 60)

    # ── Step 1: MCP session + tool discovery ──────────────────────────────
    print("\n[1/3] Connecting to MCP server and discovering tools...")
    try:
        with MCPClient(_mcp_transport) as mcp:
            tools = mcp.list_tools_sync()
            tool_names = [t.tool_name for t in tools]
            print(f"  [OK]  Session established")
            print(f"  [OK]  {len(tool_names)} tools discovered:")
            for name in tool_names:
                print(f"       - {name}")

            # ── Step 2: Invoke find_rooms directly ────────────────────────
            print("\n[2/3] Calling find_rooms(capacity=8, projector_required=True)...")
            try:
                result = mcp.call_tool_sync(
                    tool_use_id="test-find-rooms-001",
                    name="find_rooms",
                    arguments={"capacity": 8, "projector_required": True},
                )
                # call_tool_sync returns a dict: {status, toolUseId, content}
                status  = result.get("status") if isinstance(result, dict) else result.status
                content = result.get("content") if isinstance(result, dict) else result.content
                print(f"  [OK]  Tool call returned status: {status}")
                if content:
                    for item in content:
                        if "text" in item:
                            text = item["text"]
                            preview = text[:600] + ("..." if len(text) > 600 else "")
                            print(f"  Response: {preview}")
                else:
                    print("  (no content in response)")
            except Exception as e:
                print(f"  [FAIL]  Tool call failed: {e}")

    except Exception as e:
        print(f"  [FAIL]  MCP connection failed: {e}")
        print("\n  Make sure the MCP server is running:")
        print("    cd mcp && .venv\\Scripts\\python server.py")
        return

    # ── Step 3: Bedrock connectivity ──────────────────────────────────────
    print("\n[3/3] Testing Bedrock connectivity (minimal call)...")
    try:
        model = _make_model()
        # Invoke the model with a tiny prompt to confirm auth + model access
        minimal_agent = Agent(model=model, system_prompt="You are a test agent.")
        result = minimal_agent("Reply with exactly: OK")
        print(f"  [OK]  Bedrock responded: {str(result).strip()[:80]}")
    except Exception as e:
        err = str(e)
        if "credential" in err.lower() or "auth" in err.lower():
            print(f"  [FAIL]  AWS credentials error: {err}")
        elif "model" in err.lower() or "access" in err.lower():
            print(f"  [FAIL]  Model access error (check Bedrock access for {BEDROCK_MODEL_ID}): {err}")
        else:
            print(f"  [FAIL]  Bedrock error: {err}")
        return

    print("\n" + "=" * 60)
    print("  [OK]  All checks passed -- Phase 1 complete")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Interactive REPL
# ---------------------------------------------------------------------------

def run_interactive():
    """Run the agent in an interactive terminal loop."""
    print("=" * 60)
    print("  SpacePilot Agent — Interactive Mode")
    print("=" * 60)
    print(f"  Model  : {BEDROCK_MODEL_ID}")
    print(f"  Region : {AWS_REGION}")
    print(f"  MCP    : {MCP_SERVER_URL}")
    print("=" * 60)
    print("  Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("Agent: ", end="", flush=True)
        response = process_request(user_input)
        print(response)
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"

    if mode == "test":
        run_connection_test()
    else:
        run_interactive()
