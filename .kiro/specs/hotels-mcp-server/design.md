# Design: Hotels MCP Server

## Overview

Minimal FastMCP server exposing three hotel tools backed by a local JSON file. Single server.py file, no Pydantic models, plain dict returns.

## Architecture

```
hotels_mcp/
├── server.py          # FastMCP server + all tools + data loading
└── data/
    └── hotels.json    # ~15 mock hotels
```

## server.py

```python
import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("hotels-mcp-server")

# Load data at module level
_data_path = Path(__file__).parent / "data" / "hotels.json"
with open(_data_path) as f:
    _hotels = json.load(f)

@mcp.tool()
def search_hotels(city: str, checkin_date: str, checkout_date: str, guests: int = 1, max_results: int = 5) -> list[dict] | dict:
    """Search hotels in a city for given dates and guest count."""
    ...

@mcp.tool()
def get_hotel_details(hotel_id: str) -> dict:
    """Get details for a specific hotel by ID."""
    ...

@mcp.tool()
def search_hotels_by_budget(city: str, checkin_date: str, checkout_date: str, max_price_per_night: int = 0) -> list[dict] | dict:
    """Search hotels within a nightly budget. max_price_per_night is int for Cedar policy compatibility."""
    ...
```

## Data Model (hotels.json)

Each hotel record:

| Field | Type | Example |
|---|---|---|
| hotel_id | str | "HTL-001" |
| name | str | "Sakura Grand Hotel" |
| city | str | "Tokyo" |
| country | str | "Japan" |
| star_rating | int | 4 |
| price_per_night | float | 180.00 |
| currency | str | "USD" |
| amenities | list[str] | ["wifi", "pool", "gym"] |
| room_types | list[str] | ["Standard", "Deluxe", "Suite"] |
| description | str | "Modern hotel in Shinjuku..." |

## Tool Behavior

- search_hotels: filter by city (case-insensitive), sort by price_per_night asc, limit by max_results
- get_hotel_details: lookup by hotel_id, return full record or error dict
- search_hotels_by_budget: like search_hotels but also filter price_per_night <= max_price_per_night. Note: max_price_per_night is int (not float) because Cedar policies only support Long type for numeric comparisons
- All errors return {"error": "descriptive message"}, never raise exceptions
