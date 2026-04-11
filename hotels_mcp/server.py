"""Hotels MCP Server — search and retrieve hotel data."""

import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("hotels-mcp-server")

# Load hotel data at module level
_data_path = Path(__file__).parent / "data" / "hotels.json"
with open(_data_path) as f:
    _hotels: list[dict] = json.load(f)


@mcp.tool()
def search_hotels(
    city: str,
    checkin_date: str,
    checkout_date: str,
    guests: int = 1,
    max_results: int = 5,
) -> list[dict] | dict:
    """Search hotels in a city for given dates and guest count.

    Args:
        city: City name (e.g. "Tokyo", "London").
        checkin_date: Check-in date in YYYY-MM-DD format.
        checkout_date: Check-out date in YYYY-MM-DD format.
        guests: Number of guests (default 1).
        max_results: Maximum number of results to return (default 5).

    Returns:
        List of matching hotel dicts sorted by price_per_night, or error dict.
    """
    if not city or not city.strip():
        return {"error": f"Invalid city: '{city}'"}
    if guests < 1:
        return {"error": f"guests must be positive, got {guests}"}

    city_lower = city.strip().lower()
    results = [h for h in _hotels if h["city"].lower() == city_lower]
    results.sort(key=lambda h: h["price_per_night"])
    return results[:max_results]


@mcp.tool()
def get_hotel_details(hotel_id: str) -> dict:
    """Get details for a specific hotel by its ID.

    Args:
        hotel_id: Hotel identifier in HTL-XXX format (e.g. "HTL-001").

    Returns:
        Hotel details dict, or error dict if not found.
    """
    if not hotel_id or not hotel_id.strip():
        return {"error": f"Invalid hotel_id: '{hotel_id}'"}

    for h in _hotels:
        if h["hotel_id"] == hotel_id.strip():
            return h

    return {"error": f"Hotel not found: {hotel_id}"}


@mcp.tool()
def search_hotels_by_budget(
    city: str,
    checkin_date: str,
    checkout_date: str,
    max_price_per_night: int = 0,
) -> list[dict] | dict:
    """Search hotels within a nightly budget.

    Args:
        city: City name (e.g. "Paris").
        checkin_date: Check-in date in YYYY-MM-DD format.
        checkout_date: Check-out date in YYYY-MM-DD format.
        max_price_per_night: Maximum price per night (int for Cedar policy compatibility).

    Returns:
        List of matching hotel dicts sorted by price_per_night, or error dict.
    """
    if not city or not city.strip():
        return {"error": f"Invalid city: '{city}'"}
    if max_price_per_night <= 0:
        return {"error": f"max_price_per_night must be positive, got {max_price_per_night}"}

    city_lower = city.strip().lower()
    results = [
        h for h in _hotels
        if h["city"].lower() == city_lower
        and h["price_per_night"] <= max_price_per_night
    ]
    results.sort(key=lambda h: h["price_per_night"])
    return results



if __name__ == "__main__":
    import os
    if os.environ.get("MCP_TRANSPORT") == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", stateless_http=True)
    else:
        mcp.run()
