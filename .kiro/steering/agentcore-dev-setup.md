---
inclusion: manual
---

# AgentCore Dev Setup — TravelAgent

## First-Time Setup (new machine or fresh clone)

```bash
cd agentcore/cdk
npm install
cd ../..
```

This installs the CDK dependencies including `tsc`. Required before `agentcore deploy` will work. Only needed once per machine.

## Starting the Dev Server

```bash
agentcore dev --runtime TravelAgent --logs
```

- TravelAgent is the first runtime in `agentcore.json`, so it gets port **8080**
- Wait for `Application startup complete` before sending requests
- The server hot-reloads on file changes to `travel_agent/`

## Testing with curl (GitBash)

Use GitBash, not PowerShell — PowerShell aliases `curl` to `Invoke-WebRequest` and mangles `$` in strings.

```bash
curl -X POST "http://localhost:8080/invocations" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Plan a trip from SFO to Tokyo, March 10-15 2026, budget 3000 dollars"}'
```

Avoid using `$` in the prompt string — shells interpret it as a variable.

## Port Assignment

`agentcore dev` assigns ports in runtime order from `agentcore.json`:
- 1st runtime → 8080
- 2nd runtime → 8081
- 3rd runtime → 8082

TravelAgent must be first in the `runtimes` array to get port 8080.

## Windows Encoding Fix

Claude responses contain emoji (✈️, ⭐, 💰) which crash on Windows cp1252.
Fixed in `travel_agent/agent.py` with:

```python
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

This is not needed on Linux (AWS deployment).

## Token Refresh

The agent auto-refreshes its gateway OAuth token (see `gateway-token-refresh.md`).
For the Kiro MCP gateway connection in `.kiro/settings/mcp.json`, manually refresh
using the steps in `gateway-token-refresh.md`.

## Troubleshooting

| Issue | Fix |
|---|---|
| Port 8080 in use | Kill stale processes or use `--port <N>` |
| `agentcore` not found | Run from a terminal where npm global bin is on PATH |
| charmap encoding error | Ensure the `sys.stdout.reconfigure` fix is in agent.py |
| Agent says budget is "000" | Don't use `$` in prompt — use "3000 dollars" instead |
| No flights found | Include the year (2026) in the date — mock data uses 2026 |
