---
inclusion: always
---
# Travel Planner Workshop Conventions

## Project Overview
We are building a travel planner system consisting of:
1. A Flights MCP Server (FastMCP) — searches and retrieves flight data
2. A Hotels MCP Server (FastMCP) — searches and retrieves hotel data
3. A Strands Agent that orchestrates both MCP servers to plan trips

## Tech Stack
- Python 3.12+
- FastMCP 3.x for MCP servers
- Strands Agents SDK for the orchestrating agent
- Mock JSON data (no external APIs)

## FastMCP Conventions
- Use `FastMCP` class as the main entry point
- Use `@mcp.tool()` decorator for all tools
- All tools must have type hints and clear docstrings
- Return plain dicts from tools
- Load JSON data with json.load() at module level
- Handle errors gracefully — return error dicts, don't crash
- Keep each server self-contained in a single `server.py` file

## Code Style
- snake_case for functions and variables
- PascalCase for classes
- Type hints on all function signatures
- Docstrings on all public functions

## Project Structure
Each MCP server should follow:
```
server_name/
├── __init__.py
├── server.py          # FastMCP server definition + tools (entrypoint, single file)
├── data/
│   └── *.json         # Mock data files
├── pyproject.toml     # Required by AgentCore CLI for packaging
└── requirements.txt
```

## AgentCore CLI & Project Structure

This workshop uses the [AgentCore CLI](https://github.com/aws/agentcore-cli) (`@aws/agentcore`) for project scaffolding, local development, and deployment. It uses AWS CDK under the hood. Install both with:
```
npm install -g @aws/agentcore aws-cdk
```

### Creating a Project
Use `agentcore create` to scaffold a new project with `--no-runtime` (we add runtimes separately):
```bash
agentcore create --name travelplanner --no-runtime
cd travelplanner
```

This generates the project layout:
```
travel-planner/
├── agentcore/
│   ├── .env.local          # API keys (gitignored)
│   ├── agentcore.json      # Resource specifications (runtimes, memory, credentials)
│   ├── mcp.json            # Gateway and target configuration
│   ├── aws-targets.json    # Deployment targets (account, region)
│   └── cdk/                # CDK infrastructure
└── app/                    # Application code (agents live here)
```

### Adding Agents
Add existing MCP servers as BYO (bring-your-own) agents:
```bash
agentcore add runtime --name FlightsMcp --type byo --code-location ./flights_mcp --entrypoint server.py --protocol MCP
agentcore add runtime --name HotelsMcp --type byo --code-location ./hotels_mcp --entrypoint server.py --protocol MCP
```

Add a Strands agent from template:
```bash
agentcore add runtime --name TravelAgent --framework Strands --model-provider Bedrock
```

### Adding a Gateway with Targets
```bash
agentcore add gateway --name travel-planner-gateway
agentcore add gateway-target --name flights --type mcp-server --endpoint <runtime-url> --gateway travel-planner-gateway
agentcore add gateway-target --name hotels --type mcp-server --endpoint <runtime-url> --gateway travel-planner-gateway
```

### Lifecycle Commands
```
agentcore dev                        # Start local dev server with hot-reload
agentcore dev --invoke list-tools    # Test MCP tools locally
agentcore deploy -y                  # Deploy all resources to AWS
agentcore invoke "Hello"             # Invoke deployed agent
agentcore status                     # Check deployment status
agentcore remove runtime --name X      # Remove a resource
```

All resources (agents, gateways, targets, credentials) are declared in config files and deployed together with `agentcore deploy`. See the [CLI commands reference](https://github.com/aws/agentcore-cli/blob/main/docs/commands.md) for the full list of flags and options.

## Agent Code Pattern

When creating a Strands agent that connects to the AgentCore Gateway, follow this structure.

### Agent Structure
Every agent file must follow this layout in order:
1. Module docstring with description and usage
2. Imports
3. Default configuration from environment variables (fallback only)
4. System prompt as a module-level constant
5. OAuth2 token management with caching
6. MCP client factory using `streamablehttp_client` with auto-refreshing auth
7. `BedrockAgentCoreApp` entrypoint that reads gateway config from the payload
8. `if __name__ == "__main__": app.run()`

### Required Imports
```python
import os
from datetime import datetime, timedelta
import httpx
from bedrock_agentcore import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
```

### Configuration
- Hardcode gateway config values directly in the module-level defaults — do NOT use empty strings or placeholder URLs as defaults
- Use `os.environ.get()` to allow overriding via environment variables, but the hardcoded value should be the working default
- The `BedrockAgentCoreApp` runtime only passes `prompt` in the payload — it strips all other keys like `gateway_config`, so payload-based config does NOT work
- All gateway config must come from either hardcoded defaults or environment variables

```python
GATEWAY_MCP_URL = os.environ.get("GATEWAY_MCP_URL", "https://your-actual-gateway-url/mcp")
GATEWAY_CLIENT_ID = os.environ.get("GATEWAY_CLIENT_ID", "your-actual-client-id")
GATEWAY_CLIENT_SECRET = os.environ.get("GATEWAY_CLIENT_SECRET", "your-actual-client-secret")
GATEWAY_TOKEN_ENDPOINT = os.environ.get("GATEWAY_TOKEN_ENDPOINT", "https://your-actual-cognito-domain.auth.region.amazoncognito.com/oauth2/token")
GATEWAY_SCOPE = os.environ.get("GATEWAY_SCOPE", "")
```

### OAuth2 Token Management
- Use a module-level `_token_cache` dict with `token` and `expires_at` keys
- Cache tokens and refresh 5 minutes before expiry (`expires_in - 300`)
- Use `httpx.post()` with `client_credentials` grant type
- Raise `RuntimeError` on non-200 responses

### MCPClient Lifecycle — Do NOT use `with mcp_client:`
- **NEVER** manually call `mcp_client.start()` or use `with mcp_client:` as a context manager when passing the MCPClient to a Strands `Agent`.
- The `Agent` manages the MCPClient lifecycle internally. If you start it beforehand, the Agent will try to start it again and fail with: `"the client session is currently running"`.
- Just create the MCPClient and pass it directly in the `tools` list:

```python
# ✅ CORRECT — let the Agent manage the MCPClient lifecycle
mcp_client = get_mcp_client()
agent = Agent(model=model, tools=[mcp_client])
response = agent(prompt)

# ❌ WRONG — causes "client session is currently running" error
mcp_client = get_mcp_client()
with mcp_client:
    agent = Agent(model=model, tools=[mcp_client])
    response = agent(prompt)
```

### MCP Client Factory
- Use a custom `httpx.Auth` subclass inside `get_mcp_client()` so the token is refreshed on every HTTP request automatically
- Pass `auth=_OAuthAuth()` to `streamablehttp_client` instead of static headers
- Return an `MCPClient` wrapping a lambda that calls `streamablehttp_client`

```python
def get_mcp_client() -> MCPClient:
    class _OAuthAuth(httpx.Auth):
        def auth_flow(self, request):
            request.headers["Authorization"] = f"Bearer {get_oauth_token()}"
            yield request

    return MCPClient(lambda: streamablehttp_client(
        url=GATEWAY_MCP_URL,
        auth=_OAuthAuth(),
    ))
```

### Entrypoint
- Use `@app.entrypoint` decorator on the `invoke` function
- Accept `payload: dict` and optional `context: dict | None = None`
- Extract `prompt` from payload with a default fallback
- Create MCP client, create `BedrockModel` and `Agent`, invoke, return response dict
- **Note:** Do NOT try to read `gateway_config` from the payload — the runtime strips it. Use hardcoded defaults or env vars instead.

```python
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict, context: dict | None = None) -> dict:
    prompt = payload.get("prompt", "Plan me a trip!")

    mcp_client = get_mcp_client()

    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name="us-east-1",
        max_tokens=4096,
    )

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[mcp_client],
    )

    response = agent(prompt)
    return {"response": str(response)}
```

### Model Configuration
- Use `BedrockModel` with cross-region inference prefix (`us.`)
- Default model: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Set `region_name="us-east-1"`
- Set `max_tokens=4096`

### System Prompt
- Define as a module-level `SYSTEM_PROMPT` constant
- List all available tools with descriptions
- Include step-by-step instructions for the agent's workflow
- Specify data format conventions (IATA codes, date formats, etc.)

## AgentCore Memory

AgentCore Memory provides persistent context for agents across conversations.

### Adding Memory via CLI

```bash
agentcore add memory --name TravelMemory --strategies SEMANTIC,SUMMARIZATION --expiry 30
```

This adds a memory resource to `agentcore.json`:

```json
{
  "memories": [
    {
      "type": "AgentCoreMemory",
      "name": "TravelMemory",
      "eventExpiryDuration": 30,
      "strategies": [{ "type": "SEMANTIC" }, { "type": "SUMMARIZATION" }]
    }
  ]
}
```

### Memory Strategies

| Strategy | Description |
|---|---|
| SEMANTIC | Vector-based similarity search for relevant context |
| SUMMARIZATION | Compressed conversation history |
| USER_PREFERENCE | Store user-specific preferences and settings |
| EPISODIC | Capture and reflect on meaningful interaction episodes |

### Memory Shorthands (for `agentcore create` / `agentcore add runtime`)

| Shorthand | What it creates |
|---|---|
| `none` | No memory |
| `shortTerm` | Memory with no strategies (session context via event expiry only) |
| `longAndShortTerm` | Memory with SEMANTIC, USER_PREFERENCE, SUMMARIZATION, EPISODIC |

### Environment Variable

Each memory gets an env var: `MEMORY_<NAME>_ID` (uppercase, underscores).
Example: memory named `TravelMemory` → `MEMORY_TRAVELMEMORY_ID`

### Integrating Memory into a Strands Agent

1. Create a `memory/session.py` file inside the agent folder
2. Use `AgentCoreMemorySessionManager` from `bedrock_agentcore`
3. Pass the session manager to the `Agent` constructor
4. Extract `session_id` and `user_id` from the `context` object in the entrypoint

#### memory/session.py

```python
import os
from typing import Optional
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)

MEMORY_ID = os.getenv("MEMORY_TRAVELMEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-east-1")


def get_memory_session_manager(
    session_id: str, actor_id: str
) -> Optional[AgentCoreMemorySessionManager]:
    if not MEMORY_ID:
        return None

    retrieval_config = {
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
        f"/summaries/{actor_id}/{session_id}": RetrievalConfig(
            top_k=3, relevance_score=0.5
        ),
    }

    return AgentCoreMemorySessionManager(
        AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config=retrieval_config,
        ),
        REGION,
    )
```

#### Updated Entrypoint with Memory

- Use an agent cache keyed by `session_id/user_id` to reuse agents within a session
- Extract `session_id` and `user_id` from the `context` parameter
- Pass `session_manager` to the `Agent` constructor

```python
from memory.session import get_memory_session_manager

_agent_cache: dict = {}

@app.entrypoint
def invoke(payload: dict, context: dict | None = None) -> dict:
    session_id = getattr(context, "session_id", "default-session")
    user_id = getattr(context, "user_id", "default-user")
    prompt = payload.get("prompt", "Plan me a trip!")

    cache_key = f"{session_id}/{user_id}"
    if cache_key not in _agent_cache:
        mcp_client = get_mcp_client()
        session_manager = get_memory_session_manager(session_id, user_id)

        model = BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region_name="us-east-1",
            max_tokens=4096,
        )

        _agent_cache[cache_key] = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[mcp_client],
            session_manager=session_manager,
        )

    response = _agent_cache[cache_key](prompt)
    return {"response": str(response)}
```

### Deployment with Memory

Memory resources are provisioned during `agentcore deploy`:
- STM provisioning: ~30-90 seconds
- LTM provisioning: ~120-180 seconds
- Deploy waits for memory to become ACTIVE before proceeding

## AgentCore Policy (Cedar)

AgentCore Policy enables fine-grained authorization for agent tool calls using the Cedar policy language. A policy engine attaches to a gateway and evaluates every tool call against Cedar policies before allowing execution.

### Key Concepts

- **Policy Engine**: Container for Cedar policies, attached to one gateway
- **Cedar Policies**: Authorization rules using `permit` (allow) or `forbid` (deny)
- **Default deny**: Everything is blocked unless explicitly permitted
- **Forbid wins**: If any `forbid` policy matches, access is denied even if `permit` policies also match

### Action Name Format

Cedar action names follow the pattern `<gateway_target_name>___<tool_name>` (three underscores).

Example for a gateway target named `flights` with tools from the flights MCP server:
```
AgentCore::Action::"flights___search_flights"
AgentCore::Action::"flights___get_flight_details"
AgentCore::Action::"flights___search_flights_by_budget"
```

### Cedar Data Type Limitation

Cedar only supports `Long` (integers) for numeric comparisons — **not floats or decimals**. If a tool parameter is typed as `float` and you need a Cedar condition on it, change the type hint to `int` in the MCP server. Otherwise you'll get: `unexpected type: expected Long but saw decimal`.

### Policy Modes

| Mode | Behavior |
|---|---|
| `ENFORCE` | Blocks tool calls that violate policies |
| `LOG_ONLY` | Logs policy decisions but does not block anything |

**Always set mode to `ENFORCE` for policies to actually take effect.** `LOG_ONLY` is useful for testing before enforcement.

### Writing Cedar Policies

#### Permit policy (allow an action with conditions)

```cedar
permit(
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource
)
when {
  context.input.max_price <= 1000
};
```

#### Forbid policy (block an action with conditions)

```cedar
forbid(
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource
)
when {
  context.input.max_price > 1000
};
```

#### Scoped to a specific gateway

```cedar
permit(
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource == AgentCore::Gateway::"<YOUR_GATEWAY_ARN>"
)
when {
  context.input.max_price <= 1000
};
```

### Natural Language Policy Generation

AgentCore supports generating Cedar from natural language descriptions. Write clear prompts with three elements:
- **Who**: Which users/roles (e.g. "all users", "user with role admin")
- **What**: Which tool action (e.g. "call search_flights_by_budget")
- **When**: Under what conditions (e.g. "when max_price is less than or equal to 1000")

Example prompts:
```
Allow all users to call search_flights_by_budget when the max_price is less than or equal to 1000.
Forbid all users from calling search_flights_by_budget when the max_price is greater than 1000.
```

Avoid vague language like "reasonable amount" — use precise numeric comparisons.

### Adding Policy Engine via agentcore.json

Add a policy engine to the `policyEngines` array and reference it in the gateway's `policyEngineConfiguration`:

```json
{
  "policyEngines": [
    {
      "name": "travelpolicy",
      "description": "Policy engine for travel planner gateway"
    }
  ]
}
```

In the gateway config:
```json
{
  "policyEngineConfiguration": {
    "policyEngineName": "travelpolicy",
    "mode": "ENFORCE"
  }
}
```

### Verifying Policy Enforcement

1. Check agent response — blocked tool calls result in authorization errors
2. Check CloudWatch logs: `agentcore logs --agent <name> --since 5m`
3. Test directly against the gateway with `curl` using `tools/call` JSON-RPC method
4. Compare a permitted call (within limits) vs a denied call (exceeding limits)
