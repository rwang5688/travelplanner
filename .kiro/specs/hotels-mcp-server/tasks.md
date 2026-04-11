# Tasks: Hotels MCP Server

- [ ] 1. Create hotels_mcp/data/hotels.json with ~15 realistic mock hotels
  - Cities: Tokyo, London, Paris, New York, San Francisco
  - Fields: hotel_id (HTL-001 format), name, city, country, star_rating, price_per_night, currency, amenities list, room_types list, description
  - Variety in star ratings, prices, amenities

- [ ] 2. Create hotels_mcp/server.py with FastMCP server and all three tools
  - Load JSON at module level with json.load()
  - search_hotels(city, checkin_date, checkout_date, guests, max_results): filter by city, sort by price, limit results
  - get_hotel_details(hotel_id): lookup by ID, return record or error dict
  - search_hotels_by_budget(city, checkin_date, checkout_date, max_price_per_night): filter by price <= max_price_per_night (max_price_per_night is int for Cedar compatibility), sort by price
  - All tools use @mcp.tool(), have type hints and docstrings, return plain dicts
  - Error handling: return {"error": "..."} dicts, never raise exceptions
