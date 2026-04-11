---
inclusion: manual
---

# Gateway Token Refresh

The travel-planner-gateway MCP entry in `.kiro/settings/mcp.json` uses a bearer token that expires every hour.

## When the user says "refresh gateway token" or similar:

1. Read `agentcore/.env.local` to get `TRAVEL_AGENT_CLIENT_ID` and `TRAVEL_AGENT_CLIENT_SECRET`
2. POST to the token endpoint:
   ```
   https://travel-agent-539307129890.auth.us-east-1.amazoncognito.com/oauth2/token
   ```
   with `grant_type=client_credentials`, `scope=travel-agent/access`, and Basic auth using the client ID and secret.
3. If `agentcore/.env.local` is empty, run the Cognito discovery script from GitBash (NOT PowerShell) with `AWS_DEFAULT_REGION` set:
   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   # then run the cognito pool discovery script
   ```
3. Extract the `access_token` from the response.
4. Update the `Authorization` header in `.kiro/settings/mcp.json` under the `travel-planner-gateway` entry with `Bearer <new_token>`.

## Quick command (Python):
```python
import httpx
r = httpx.post(
    'https://travel-agent-539307129890.auth.us-east-1.amazoncognito.com/oauth2/token',
    data={'grant_type': 'client_credentials', 'scope': 'travel-agent/access'},
    auth=('<CLIENT_ID>', '<CLIENT_SECRET>'),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
print(r.json()['access_token'])
```

## Token details
- Issuer: Cognito travel-agent-pool (us-east-1_ENRlyj7yg)
- Scope: travel-agent/access
- Expiry: ~3600 seconds (1 hour)
