# Requirements: Hotels MCP Server

## Requirement 1: Search Hotels

**User Story:** As a travel planning agent, I want to search for hotels in a city for given dates and guest count.

### Acceptance Criteria

1. WHEN a search includes city, checkin_date, checkout_date, and guests THEN the system SHALL return all hotels in that city (case-insensitive)
2. WHEN results match THEN the system SHALL sort by price_per_night ascending
3. WHEN a max_results parameter is provided THEN the system SHALL limit results to that number
4. WHEN no hotels match THEN the system SHALL return an empty list
5. WHEN invalid inputs are provided THEN the system SHALL return an error dict

## Requirement 2: Get Hotel Details

**User Story:** As a travel planning agent, I want to retrieve full details for a specific hotel by its ID.

### Acceptance Criteria

1. WHEN a valid hotel_id is provided THEN the system SHALL return the complete hotel record as a dict
2. WHEN an invalid or non-existent hotel_id is provided THEN the system SHALL return an error dict

## Requirement 3: Search Hotels by Budget

**User Story:** As a travel planning agent, I want to search for hotels within a nightly budget.

### Acceptance Criteria

1. WHEN a search includes city, checkin_date, checkout_date, and max_price_per_night THEN the system SHALL return hotels with price_per_night <= max_price_per_night
2. WHEN results match THEN the system SHALL sort by price_per_night ascending
3. WHEN no hotels match THEN the system SHALL return an empty list
4. WHEN invalid inputs are provided THEN the system SHALL return an error dict

## Requirement 4: FastMCP Server

**User Story:** As a developer, I want the server to expose tools via FastMCP so any MCP-compatible agent can discover and call them.

### Acceptance Criteria

1. WHEN the server starts THEN it SHALL register search_hotels, get_hotel_details, and search_hotels_by_budget tools using @mcp.tool()
2. All tools SHALL have type hints and clear docstrings
3. All tools SHALL return plain dicts

## Requirement 5: Mock Data

**User Story:** As a developer, I want hotel data sourced from a local JSON file with no external dependencies.

### Acceptance Criteria

1. The server SHALL load ~15 hotels from data/hotels.json at module level using json.load()
2. Hotel records SHALL include: hotel_id (HTL-001 format), name, city, country, star_rating, price_per_night, currency, amenities list, room_types list, description
