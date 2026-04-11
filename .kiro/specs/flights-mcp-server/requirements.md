# Requirements: Flights MCP Server

## Requirement 1: Search Flights

**User Story:** As a travel planning agent, I want to search for flights by origin, destination, and date, so that I can find available flight options for users.

### Acceptance Criteria

1. WHEN a search request includes origin and destination airport codes THEN the system SHALL return all flights matching those airports (case-insensitive)
2. WHEN a search request includes a date THEN the system SHALL filter results to only flights on that date
3. WHEN a max_results parameter is provided THEN the system SHALL limit the returned results to that number
4. WHEN no flights match the search criteria THEN the system SHALL return an empty list with no errors
5. WHEN invalid inputs are provided THEN the system SHALL return an error dict with a descriptive message

## Requirement 2: Get Flight Details

**User Story:** As a travel planning agent, I want to retrieve detailed information about a specific flight by its ID.

### Acceptance Criteria

1. WHEN a valid flight ID is provided THEN the system SHALL return the complete flight record as a dict
2. WHEN an invalid or non-existent flight ID is provided THEN the system SHALL return an error dict

## Requirement 3: Search Flights by Budget

**User Story:** As a travel planning agent, I want to search for flights within a price limit.

### Acceptance Criteria

1. WHEN a search includes origin, destination, date, and max_price THEN the system SHALL return flights with price <= max_price
2. WHEN results match THEN the system SHALL sort them by price ascending
3. WHEN no flights match THEN the system SHALL return an empty list
4. WHEN invalid inputs are provided THEN the system SHALL return an error dict

## Requirement 4: FastMCP Server

**User Story:** As a developer, I want the server to expose tools via FastMCP so any MCP-compatible agent can discover and call them.

### Acceptance Criteria

1. WHEN the server starts THEN it SHALL register search_flights, get_flight_details, and search_flights_by_budget tools using @mcp.tool()
2. All tools SHALL have type hints and clear docstrings
3. All tools SHALL return plain dicts

## Requirement 5: Mock Data

**User Story:** As a developer, I want flight data sourced from a local JSON file with no external dependencies.

### Acceptance Criteria

1. The server SHALL load ~20 flights from data/flights.json at module level using json.load()
2. Flight records SHALL include: flight_id (FL-001 format), airline, flight_number, origin, destination, departure_time, arrival_time, price, currency, seats_available
