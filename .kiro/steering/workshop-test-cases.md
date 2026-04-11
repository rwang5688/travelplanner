---
inclusion: auto
---

# Workshop Test Cases

These are the canonical sample queries that all MCP servers and the orchestrating agent must support. Use these to validate correctness during and after implementation.

## Flights MCP Server

1. Search for flights from SFO to TYO on March 10, 2026
   - Tool: `search_flights(origin="SFO", destination="TYO", date="2026-03-10")`
   - Expected: Returns flights sorted by price ascending (empty list is OK if no flights match that date)

2. Find me flights from SFO to Tokyo under $900
   - Tool: `search_flights_by_budget(origin="SFO", destination="TYO", max_price=900)`
   - Expected: Returns only flights with price <= 900, sorted by price ascending

3. Get details for flight FL-001
   - Tool: `get_flight_details(flight_id="FL-001")`
   - Expected: Returns complete flight record for FL-001

## Hotels MCP Server

4. Search for hotels in Tokyo for March 10-15, 2026, 2 guests
   - Tool: `search_hotels(city="Tokyo", checkin_date="2026-03-10", checkout_date="2026-03-15", guests=2)`
   - Expected: Returns Tokyo hotels sorted by price_per_night ascending

5. Find hotels in Tokyo under $200 per night
   - Tool: `search_hotels_by_budget(city="Tokyo", checkin_date="2026-03-10", checkout_date="2026-03-15", max_price_per_night=200)`
   - Expected: Returns only Tokyo hotels with price_per_night <= 200, sorted ascending

6. Get details for hotel HTL-001
   - Tool: `get_hotel_details(hotel_id="HTL-001")`
   - Expected: Returns complete hotel record for HTL-001 including amenities, room_types, description

## Combined Query (Strands Agent)

7. "I'm planning a trip from SFO to Tokyo, March 10-15. Can you find me flights and hotels? My budget is about $3000 total."
   - Agent should call both flights and hotels MCP servers
   - Flights: `search_flights(origin="SFO", destination="TYO", date="2026-03-10")` or `search_flights_by_budget(...)`
   - Hotels: `search_hotels(city="Tokyo", checkin_date="2026-03-10", checkout_date="2026-03-15")` or `search_hotels_by_budget(...)`
   - Expected: Agent presents combined flight + hotel options within ~$3000 total budget

## Validation Rules

- During task execution, always verify that mock data supports these queries (e.g. Tokyo hotels exist, SFO-TYO flights exist, HTL-001 and FL-001 exist)
- After implementing each tool, mentally trace through the relevant test cases above
- Mock data must include price variety so budget queries return meaningful filtered results
- Parameter names must match the actual tool signatures exactly (checkin_date, checkout_date, max_price, max_price_per_night)

## AgentCore Dev Test Cases

Prerequisites:

```bash
export AWS_DEFAULT_REGION=us-east-1
```

```bash
<Apply AWS temp credentials>
```

Start the dev server:

```bash
agentcore dev --runtime TravelAgent --logs
```

Test from GitBash (not PowerShell):

```bash
curl -X POST "http://localhost:8080/invocations" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Plan a trip from SFO to Tokyo, March 10-15 2026, budget 3000 dollars"}'
```

## AgentCore Invoke Test Cases

Prerequisites (same as above):

```bash
export AWS_DEFAULT_REGION=us-east-1
```

```bash
<Apply AWS temp credentials>
```

Test cases:

```bash
agentcore invoke --runtime TravelAgent "Plan me a 5-day trip to Tokyo from San Francisco, departing March 10, 2026. My budget is around 3000 dollars total for flights and hotel. I prefer direct flights if available."
```

```bash
agentcore invoke --runtime TravelAgent "Find me the cheapest way to get to Tokyo from LAX next month. I'm on a tight budget."
```

```bash
agentcore invoke --runtime TravelAgent "Plan a luxury trip to Paris from JFK, March 20-25 2026. Money is not an issue."
```

```bash
agentcore invoke --runtime TravelAgent "I need to go to London from SFO, March 15-20 2026. Budget is 2500 dollars. I prefer direct flights and hotels with a gym."
```

## AgentCore Memory Test Cases

### travel-planner-agent-trip-session-001

```bash
agentcore invoke --runtime TravelAgent \
  --session-id "travel-planner-agent-trip-session-001" \
  "Plan a 5-day trip to Tokyo from SFO, March 10-15 2026. Budget is $3000. I prefer direct flights."
```

```bash
agentcore invoke --runtime TravelAgent \
  --session-id "travel-planner-agent-trip-session-001" \
  "Can you show important places in my destination"
```

```bash
agentcore invoke --runtime TravelAgent \       
  --session-id "travel-planner-agent-trip-session-001" \
  "Summarize my trip"
```

### travel-planner-agent-trip-session-002

```bash
agentcore invoke --runtime TravelAgent \       
  --session-id "travel-planner-agent-trip-session-002" \
  "Now plan me a trip to Paris from JFK, March 20-25 2026."
```

```bash
agentcore invoke --runtime TravelAgent \
  --session-id "travel-planner-agent-trip-session-002" \
  "What do you remember about my travel preferences?"
```


## AgentCore Policy Test Cases

Policy: `flight_budget_limit` — permits `search_flights_by_budget` only when `max_price <= 1000`.

### Test 1: Over budget (should be BLOCKED)

```bash
agentcore invoke --runtime TravelAgent "Search flights from SFO to TYO on 2026-03-10 with max price 1500"
```

Expected: The agent should receive an authorization error when calling `search_flights_by_budget` with `max_price=1500`. The policy engine should deny the tool call.

### Test 2: Under budget (should be ALLOWED)

```bash
agentcore invoke --runtime TravelAgent "Search flights from SFO to TYO on 2026-03-10 with max price 900"
```

Expected: The agent should successfully call `search_flights_by_budget` with `max_price=900` and return matching flights (FL-002 at $720, FL-001 at $850).
