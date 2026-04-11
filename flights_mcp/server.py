"""Flights MCP Server — search and retrieve flight data."""

import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("flights-mcp-server")

# Load flight data at module level
_data_path = Path(__file__).parent / "data" / "flights.json"
with open(_data_path) as f:
    _flights: list[dict] = json.load(f)


@mcp.tool()
def search_flights(
    origin: str, destination: str, date: str = "", max_results: int = 5
) -> list[dict] | dict:
    """Search flights by origin airport, destination airport, and optional date.

    Args:
        origin: IATA airport code (e.g. "SFO").
        destination: IATA airport code (e.g. "TYO").
        date: Optional departure date in YYYY-MM-DD format.
        max_results: Maximum number of results to return (default 5).

    Returns:
        List of matching flight dicts sorted by price, or error dict.
    """
    if not origin or not origin.strip():
        return {"error": f"Invalid origin: '{origin}'"}
    if not destination or not destination.strip():
        return {"error": f"Invalid destination: '{destination}'"}

    origin_upper = origin.strip().upper()
    dest_upper = destination.strip().upper()

    results = [
        f for f in _flights
        if f["origin"].upper() == origin_upper
        and f["destination"].upper() == dest_upper
    ]

    if date:
        results = [
            f for f in results
            if f["departure_time"].startswith(date)
        ]

    results.sort(key=lambda f: f["price"])
    return results[:max_results]


@mcp.tool()
def get_flight_details(flight_id: str) -> dict:
    """Get details for a specific flight by its ID.

    Args:
        flight_id: Flight identifier in FL-XXX format (e.g. "FL-001").

    Returns:
        Flight details dict, or error dict if not found.
    """
    if not flight_id or not flight_id.strip():
        return {"error": f"Invalid flight_id: '{flight_id}'"}

    for f in _flights:
        if f["flight_id"] == flight_id.strip():
            return f

    return {"error": f"Flight not found: {flight_id}"}


@mcp.tool()
def search_flights_by_budget(
    origin: str, destination: str, date: str = "", max_price: int = 0
) -> list[dict] | dict:
    """Search flights within a budget.

    Args:
        origin: IATA airport code (e.g. "SFO").
        destination: IATA airport code (e.g. "TYO").
        date: Optional departure date in YYYY-MM-DD format.
        max_price: Maximum ticket price (int for Cedar policy compatibility).

    Returns:
        List of matching flight dicts sorted by price, or error dict.
    """
    if not origin or not origin.strip():
        return {"error": f"Invalid origin: '{origin}'"}
    if not destination or not destination.strip():
        return {"error": f"Invalid destination: '{destination}'"}
    if max_price <= 0:
        return {"error": f"max_price must be positive, got {max_price}"}

    origin_upper = origin.strip().upper()
    dest_upper = destination.strip().upper()

    results = [
        f for f in _flights
        if f["origin"].upper() == origin_upper
        and f["destination"].upper() == dest_upper
        and f["price"] <= max_price
    ]

    if date:
        results = [
            f for f in results
            if f["departure_time"].startswith(date)
        ]

    results.sort(key=lambda f: f["price"])
    return results



if __name__ == "__main__":
    import os
    if os.environ.get("MCP_TRANSPORT") == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", stateless_http=True)
    else:
        mcp.run()
