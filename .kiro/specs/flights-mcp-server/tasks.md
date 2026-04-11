# Tasks: Flights MCP Server

- [ ] 1. Create flights_mcp/data/flights.json with ~20 realistic mock flights
  - Routes: SFO->TYO, LAX->LHR, JFK->CDG, ORD->FCR, SFO->LHR, JFK->TYO, LAX->CDG, etc.
  - Fields: flight_id (FL-001 format), airline, flight_number, origin, destination, departure_time, arrival_time, price, currency, seats_available
  - Variety in airlines, prices, times, seat availability

- [ ] 2. Create flights_mcp/server.py with FastMCP server and all three tools
  - Load JSON at module level with json.load()
  - search_flights(origin, destination, date, max_results): filter, sort by price, limit results
  - get_flight_details(flight_id): lookup by ID, return record or error dict
  - search_flights_by_budget(origin, destination, date, max_price): filter by price <= max_price (max_price is int for Cedar compatibility), sort by price
  - All tools use @mcp.tool(), have type hints and docstrings, return plain dicts
  - Error handling: return {"error": "..."} dicts, never raise exceptions
