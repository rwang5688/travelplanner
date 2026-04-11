---
inclusion: always
---

# MCP Server Transport Configuration

Both MCP servers (flights_mcp, hotels_mcp) support dual transport modes controlled by the `MCP_TRANSPORT` environment variable.

## Local Development (Kiro MCP / STDIO)
- No env var needed — defaults to STDIO transport
- Kiro MCP config runs: `python flights_mcp/server.py` (no special env)

## AgentCore Runtime Deployment (Streamable HTTP)
- Set `MCP_TRANSPORT=streamable-http` to use HTTP transport on 0.0.0.0:8000
- This can be set in:
  1. `agentcore.json` under the runtime's environment variables
  2. The container Dockerfile or entrypoint script
  3. `agentcore/agentcore.json` env block for the runtime

### Example: agentcore.json env config
```json
{
  "agents": [{
    "name": "FlightsMcp",
    "environment": {
      "MCP_TRANSPORT": "streamable-http"
    }
  }]
}
```

### Example: Dockerfile
```dockerfile
ENV MCP_TRANSPORT=streamable-http
CMD ["python", "server.py"]
```

## If deployment fails
- Check that `MCP_TRANSPORT` is set to `streamable-http` in the runtime environment
- If the server starts but tools aren't reachable, verify it's binding to `0.0.0.0` (not `127.0.0.1`)
- If running locally after deployment changes, make sure `MCP_TRANSPORT` is NOT set (or unset it)
