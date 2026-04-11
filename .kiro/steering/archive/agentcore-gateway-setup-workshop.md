---
inclusion: manual
---

> **NOTE (2026-04-07):** This document was written using the older AgentCore CLI
> (`workshop_helper.py` / manual gateway creation workflow). The current project uses
> the newer CDK-based AgentCore CLI where the gateway is declared in `agentcore.json`
> and deployed via `agentcore deploy`. These values are from the old us-west-2
> deployment. Current gateway config is in `agentcore/agentcore.json` (us-east-1).
> Kept for historical reference.

# AgentCore Gateway Setup — Workshop Account

## Prerequisites

Both MCP server runtimes must be deployed and verified before gateway setup:
- flights_mcp: `arn:aws:bedrock-agentcore:us-west-2:205566541104:runtime/flights_mcp-QQJEN7HSMH` (READY, 3 tools)
- hotels_mcp: `arn:aws:bedrock-agentcore:us-west-2:205566541104:runtime/hotels_mcp-VQcGpX64jE` (READY, 3 tools)

OAuth values are in `agentcore-auth-setup-workshop.md`.

## Step 5: Create the Gateway

```bash
python workshop_helper.py create-gateway travel-planner-gateway
```

Save the Gateway ID from the output (format: `travel-planner-gateway-XXXXXXXXXX`).

| Key              | Value                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------|
| Gateway ID       | travel-planner-gateway-3tpuaj9ihi                                                                  |
| Gateway URL      | https://travel-planner-gateway-3tpuaj9ihi.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp    |
| Gateway ARN      | arn:aws:bedrock-agentcore:us-west-2:205566541104:gateway/travel-planner-gateway-3tpuaj9ihi          |
| Gateway Auth Pool| us-west-2_yEX6jMQKo                                                                                |
| Gateway Client ID| 6j8il5fbejmisjpjchpu6jj8s3                                                                         |
| Region           | us-west-2                                                                                          |

## Step 6: Set Up Gateway Authentication (Credential Providers)

Create credential providers so the gateway can authenticate to each runtime.

**IMPORTANT:** You MUST run each command from inside the corresponding server directory, or the credential provider will not be saved to `.bedrock_agentcore.yaml`.

### flights_mcp credential provider

```bash
cd flights_mcp
agentcore identity create-credential-provider \
  --name flights-mcp-identity \
  --type cognito \
  --client-id 58f4pedffurf155fmo979tku2f \
  --client-secret 1saei55eho87jvf4nhn95bo71cc8686rshhn566qi72h8g6pl9kp \
  --discovery-url https://cognito-idp.us-west-2.amazonaws.com/us-west-2_fmQIOJRyX/.well-known/openid-configuration \
  --region us-west-2 \
  --cognito-pool-id us-west-2_fmQIOJRyX
```

### hotels_mcp credential provider

```bash
cd ../hotels_mcp
agentcore identity create-credential-provider \
  --name hotels-mcp-identity \
  --type cognito \
  --client-id 158q15b5v8f58nq4r47oieo4o6 \
  --client-secret i85l1f2rlaifmqnvli5atetgdqj1e577nbs516lenia8f829kmf \
  --discovery-url https://cognito-idp.us-west-2.amazonaws.com/us-west-2_azCMLVZAl/.well-known/openid-configuration \
  --region us-west-2 \
  --cognito-pool-id us-west-2_azCMLVZAl
cd ..
```

These values come from `python workshop_helper.py setup-auth` for each server (see `agentcore-auth-setup-workshop.md`).

## Step 7: Add Runtimes as Gateway Targets

```bash
python workshop_helper.py add-target travel-planner-gateway-3tpuaj9ihi flights_mcp
```

```bash
python workshop_helper.py add-target travel-planner-gateway-3tpuaj9ihi hotels_mcp
```

Each command creates the OAuth credential provider (if not already created in Step 6) and gateway target, then waits for READY status.

| Target           | Target ID    | Status                                            |
|------------------|--------------|---------------------------------------------------|
| flights_mcp      | 2DX9EHRIIX   | ✅ READY                                          |
| hotels_mcp       | UPXUL7JNGM   | ✅ READY                                          |

## Step 8: Get the Gateway URL

```bash
python workshop_helper.py gateway-info travel-planner-gateway-3tpuaj9ihi
```

Expected output includes:
- Gateway URL (format: `https://<gateway-name>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp`)
- Bearer Token (for testing)
- Environment variables to export for the Strands agent

| Key                    | Value                                                                                              |
|------------------------|----------------------------------------------------------------------------------------------------|
| Gateway URL            | https://travel-planner-gateway-3tpuaj9ihi.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp    |
| GATEWAY_MCP_URL        | https://travel-planner-gateway-3tpuaj9ihi.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp    |
| GATEWAY_CLIENT_ID      | 6j8il5fbejmisjpjchpu6jj8s3                                                                         |
| GATEWAY_CLIENT_SECRET  | 1mvhsecsinkdr3kusk6mufpmftg9t61isfm6ns709der64sbolga                                               |
| GATEWAY_TOKEN_ENDPOINT | https://agentcore-f735022e.auth.us-west-2.amazoncognito.com/oauth2/token                           |
| GATEWAY_SCOPE          | travel-planner-gateway/invoke                                                                      |

## Review Notes

See `agentcore-deploy-issues.md` for all defects and review questions raised during this walkthrough.
