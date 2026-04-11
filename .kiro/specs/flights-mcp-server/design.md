# Design: Flights MCP Server

## Overview

Minimal FastMCP server exposing three flight tools backed by a local JSON file. Single server.py file, no Pydantic models, plain dict returns.

## Architecture

```
flights_mcp/
├── server.py          # FastMCP server + all tools + data loading
└── data/
    └── flights.json   # ~20 mock flights
```

## server.py

```python
import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("flights-mcp-server")

# Load data at module level
_data_path = Path(__file__).parent / "data" / "flights.json"
with open(_data_path) as f:
    _flights = json.load(f)

@mcp.tool()
def search_flights(origin: str, destination: str, date: str = "", max_results: int = 5) -> list[dict] | dict:
    """Search flights by origin, destination, and optional date."""
    ...

@mcp.tool()
def get_flight_details(flight_id: str) -> dict:
    """Get details for a specific flight by ID."""
    ...

@mcp.tool()
def search_flights_by_budget(origin: str, destination: str, date: str = "", max_price: int = 0) -> list[dict] | dict:
    """Search flights within a budget. max_price is int for Cedar policy compatibility."""
    ...
```

## Data Model (flights.json)

Each flight record:

| Field | Type | Example |
|---|---|---|
| flight_id | str | "FL-001" |
| airline | str | "SkyWay Airlines" |
| flight_number | str | "SW-100" |
| origin | str | "SFO" |
| destination | str | "TYO" |
| departure_time | str | "2025-08-15T08:00:00" |
| arrival_time | str | "2025-08-15T16:30:00" |
| price | float | 850.00 |
| currency | str | "USD" |
| seats_available | int | 45 |

## Tool Behavior

- search_flights: filter by origin+destination (case-insensitive), optionally by date, sort by price asc, limit by max_results
- get_flight_details: lookup by flight_id, return full record or error dict
- search_flights_by_budget: like search_flights but also filter price <= max_price. Note: max_price is int (not float) because Cedar policies only support Long type for numeric comparisons
- All errors return {"error": "descriptive message"}, never raise exceptions
