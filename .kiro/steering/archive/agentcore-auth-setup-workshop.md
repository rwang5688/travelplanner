---
inclusion: manual
---

> **NOTE (2026-04-07):** This document was written using the older AgentCore CLI
> (`agentcore configure` / `.bedrock_agentcore.yaml` / `workshop_helper.py` workflow).
> The current project uses the newer CDK-based AgentCore CLI. These OAuth values are
> from the old us-west-2 deployment. Current credentials are in `agentcore/.env.local`
> and `agentcore/agentcore.json` (us-east-1). Kept for historical reference.

# AgentCore Auth & Deploy — flights_mcp

## OAuth Values (from setup-auth)

| Key              | Value                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------|
| Discovery URL    | https://cognito-idp.us-west-2.amazonaws.com/us-west-2_fmQIOJRyX/.well-known/openid-configuration  |
| Client ID        | 58f4pedffurf155fmo979tku2f                                                                         |
| Client Secret    | 1saei55eho87jvf4nhn95bo71cc8686rshhn566qi72h8g6pl9kp                                               |
| Audience         | LEAVE BLANK (Cognito client_credentials tokens have no `aud` claim — any value causes 401)         |
| Scope            | flights-mcp/access                                                                                 |
| Pool ID          | us-west-2_fmQIOJRyX                                                                               |
| Region           | us-west-2                                                                                          |

## Existing AWS Resources (reuse during configure)

| Resource         | Value                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------|
| Execution Role   | arn:aws:iam::205566541104:role/AmazonBedrockAgentCoreSDKRuntime-us-west-2-7840733a8f               |
| ECR Repository   | 205566541104.dkr.ecr.us-west-2.amazonaws.com/bedrock-agentcore-flights_mcp                         |
| Agent ARN        | arn:aws:bedrock-agentcore:us-west-2:205566541104:runtime/flights_mcp-QQJEN7HSMH                    |
| Entrypoint       | __main__.py                                                                                             |

---

# AgentCore Auth & Deploy — hotels_mcp

## OAuth Values (from setup-auth)

| Key              | Value                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------|
| Discovery URL    | https://cognito-idp.us-west-2.amazonaws.com/us-west-2_azCMLVZAl/.well-known/openid-configuration   |
| Client ID        | 158q15b5v8f58nq4r47oieo4o6                                                                        |
| Client Secret    | i85l1f2rlaifmqnvli5atetgdqj1e577nbs516lenia8f829kmf                                               |
| Audience         | LEAVE BLANK (Cognito client_credentials tokens have no `aud` claim — any value causes 401)         |
| Scope            | hotels-mcp/access                                                                                  |
| Pool ID          | us-west-2_azCMLVZAl                                                                                |
| Region           | us-west-2                                                                                          |

## Existing AWS Resources (reuse during configure)

| Resource         | Value                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------|
| Execution Role   | arn:aws:iam::205566541104:role/AmazonBedrockAgentCoreSDKRuntime-us-west-2-7840733a8f               |
| ECR Repository   | 205566541104.dkr.ecr.us-west-2.amazonaws.com/bedrock-agentcore-hotels_mcp                          |
| Agent ARN        | arn:aws:bedrock-agentcore:us-west-2:205566541104:runtime/hotels_mcp-VQcGpX64jE                     |
| Entrypoint       | __main__.py                                                                                        |
