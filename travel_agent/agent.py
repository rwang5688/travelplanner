"""Travel Planner Agent — orchestrates flights and hotels MCP servers via AgentCore Gateway.

Usage:
    agentcore dev --runtime TravelAgent
    agentcore invoke "Plan me a trip from SFO to Tokyo, March 10-15, budget $3000"
"""

import os
import sys

# Fix Windows cp1252 encoding for emoji/unicode in Claude responses
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta

import httpx
from bedrock_agentcore import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from memory.session import get_memory_session_manager

# ---------------------------------------------------------------------------
# Gateway configuration — hardcoded defaults, overridable via env vars
# ---------------------------------------------------------------------------
GATEWAY_MCP_URL = os.environ.get(
    "GATEWAY_MCP_URL",
    "https://travelplanner-travel-planner-gateway-me5u5t9ltj.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
)
GATEWAY_CLIENT_ID = os.environ.get(
    "GATEWAY_CLIENT_ID",
    "411vlc1lsn3kh0eer61pdsiq00",
)
GATEWAY_CLIENT_SECRET = os.environ.get(
    "GATEWAY_CLIENT_SECRET",
    "1m35n9f8mgiokc5tps0fpo31819gktb30bb8dddbjeg92dg4vcc7",
)
GATEWAY_TOKEN_ENDPOINT = os.environ.get(
    "GATEWAY_TOKEN_ENDPOINT",
    "https://travel-agent-539307129890.auth.us-east-1.amazoncognito.com/oauth2/token",
)
GATEWAY_SCOPE = os.environ.get("GATEWAY_SCOPE", "travel-agent/access")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a travel planning assistant. You help users plan trips by
searching for flights and hotels using the available tools.

Available tools:
- search_flights(origin, destination, date, max_results): Search flights by route and date
- get_flight_details(flight_id): Get full details for a specific flight
- search_flights_by_budget(origin, destination, date, max_price): Search flights within a budget
- search_hotels(city, checkin_date, checkout_date, guests, max_results): Search hotels in a city
- get_hotel_details(hotel_id): Get full details for a specific hotel
- search_hotels_by_budget(city, checkin_date, checkout_date, max_price_per_night): Search hotels within a nightly budget

Workflow:
1. Parse the user's trip request (origin, destination, dates, budget, preferences)
2. Search for flights using the origin IATA code and destination IATA code
3. Search for hotels in the destination city
4. Consider the total budget: flight cost + (hotel per night * number of nights)
5. Present a structured itinerary with recommended flight and hotel options
6. Include prices and total estimated cost

Data conventions:
- Airport codes are IATA format (e.g. SFO, TYO, LHR, CDG)
- Dates are YYYY-MM-DD format
- Prices are in USD
- Hotel prices are per night
"""

# ---------------------------------------------------------------------------
# OAuth2 token management with caching
# ---------------------------------------------------------------------------
_token_cache: dict = {"token": None, "expires_at": 0.0}


def get_oauth_token() -> str:
    """Fetch or return cached OAuth2 token, refreshing 5 min before expiry."""
    now = datetime.now().timestamp()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    resp = httpx.post(
        GATEWAY_TOKEN_ENDPOINT,
        data={"grant_type": "client_credentials", "scope": GATEWAY_SCOPE},
        auth=(GATEWAY_CLIENT_ID, GATEWAY_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Token fetch failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"] - 300
    return _token_cache["token"]


# ---------------------------------------------------------------------------
# MCP client factory with auto-refreshing auth
# ---------------------------------------------------------------------------
def get_mcp_client() -> MCPClient:
    """Create an MCPClient that auto-refreshes the OAuth token on each request."""

    class _OAuthAuth(httpx.Auth):
        def auth_flow(self, request):
            request.headers["Authorization"] = f"Bearer {get_oauth_token()}"
            yield request

    return MCPClient(
        lambda: streamablehttp_client(url=GATEWAY_MCP_URL, auth=_OAuthAuth())
    )


# ---------------------------------------------------------------------------
# BedrockAgentCoreApp entrypoint
# ---------------------------------------------------------------------------
app = BedrockAgentCoreApp()

_agent_cache: dict = {}


@app.entrypoint
def invoke(payload: dict, context: dict | None = None) -> dict:
    session_id = getattr(context, "session_id", None) or "default-session"
    user_id = getattr(context, "user_id", None) or "default-user"
    prompt = payload.get("prompt", "Plan me a trip from SFO to Tokyo, March 10-15, budget $3000")

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


if __name__ == "__main__":
    app.run()
