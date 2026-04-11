# AgentCore Policy Engine Setup

## Overview
Steps to add Cedar policy-based authorization to the travel planner gateway.

## Step 1: Add Policy Engine to agentcore.json

Add a policy engine entry to the `policyEngines` array:

```json
{
  "policyEngines": [
    {
      "name": "travelpolicy",
      "description": "Policy engine for travel planner gateway"
    }
  ]
}
```

## Step 2: Attach Policy Engine to Gateway

Add `policyEngineConfiguration` to the gateway in `agentCoreGateways`:

```json
{
  "policyEngineConfiguration": {
    "policyEngineName": "travelpolicy",
    "mode": "ENFORCE"
  }
}
```

Use `LOG_ONLY` mode first for testing, then switch to `ENFORCE` when ready.

## Step 3: Deploy

```bash
agentcore deploy -y
```

This provisions the policy engine and attaches it to the gateway.

## Step 4: Add Cedar Policies

Cedar action names follow the pattern `<gateway_target_name>___<tool_name>` (three underscores).

Example actions for this project:
- `AgentCore::Action::"flights___search_flights"`
- `AgentCore::Action::"flights___search_flights_by_budget"`
- `AgentCore::Action::"flights___get_flight_details"`
- `AgentCore::Action::"hotels___search_hotels"`
- `AgentCore::Action::"hotels___search_hotels_by_budget"`
- `AgentCore::Action::"hotels___get_hotel_details"`

### Adding Policies via CLI (recommended: use --source with a .cedar file)

The `--statement` flag has severe quoting issues on Windows/PowerShell — Cedar requires double quotes around entity names which conflict with shell escaping. Use `--source` instead:

1. Write the Cedar policy to a `.cedar` file:

```cedar
// flight_budget_policy.cedar
permit (
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource == AgentCore::Gateway::"<GATEWAY-ARN>"
) when {
  context.input.max_price <= 1000
};
```

2. Add via CLI:

```bash
agentcore add policy --engine "policyengine" --name "flight_budget_limit" --description "Allow flight budget searches only under 1000" --source "flight_budget_policy.cedar"
```

3. Deploy:

```bash
agentcore deploy -y
```

### CLI Gotchas

- `agentcore add policy` auto-adds `validationMode: FAIL_ON_ANY_FINDINGS` which can cause "Resource stabilization failed" on deploy. If this happens, try changing to `IGNORE_ALL_FINDINGS` or removing the field.
- `--statement` flag on PowerShell strips double quotes from Cedar entity names — always use `--source` with a `.cedar` file instead.
- Deploy the policy engine + gateway attachment FIRST (with empty policies), then add policies in a second deploy. Doing both at once can fail.

### Example: Budget cap on flight searches

Cedar requires a `has` check for optional attributes — without it, policy creation fails with "unable to guarantee safety of access to optional attribute".

```cedar
permit (
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource == AgentCore::Gateway::"<GATEWAY-ARN>"
) when {
  context.input has max_price && context.input.max_price <= 1000
};
```

### Example: Block expensive hotel searches

```cedar
forbid (
  principal,
  action == AgentCore::Action::"hotels___search_hotels_by_budget",
  resource == AgentCore::Gateway::"<GATEWAY-ARN>"
) when {
  context.input has max_price_per_night && context.input.max_price_per_night > 500
};
```

## Important Notes

- Default deny: everything is blocked unless explicitly permitted
- Forbid wins: if any `forbid` matches, access is denied even if `permit` also matches
- Cedar only supports `Long` (integers) for numeric comparisons — change `float` type hints to `int` in MCP servers if needed
- Use `agentcore logs --agent TravelAgent --since 5m` to check policy decisions
