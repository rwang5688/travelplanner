# Implementation Plan: Deploy Streamlit App

## Overview

Create a standalone Python CDK project at `deploy-streamlit-app/` that packages the Travel Planner Streamlit app into a Docker container and deploys it on AWS ECS Fargate with Cognito authentication, ALB, and CloudFront. The implementation adapts the existing `streamlit_app/` code into a containerized version with a flat module structure (`app.py`, `cognito_client.py`, `agent_client.py`, `config_file.py`) and provisions all infrastructure via CDK.

## Tasks

- [x] 1. Create project scaffolding and configuration module
  - [x] 1.1 Create `deploy-streamlit-app/docker_app/config_file.py` with `Config` class defining `STACK_NAME = "TravelPlanner"`, `CUSTOM_HEADER_VALUE`, `SECRETS_MANAGER_ID` (derived from stack name), and `DEPLOYMENT_REGION`. Use `-agent-ui` suffix for resource names (ALB: `TravelPlanner-agent-ui`, ECS service: `TravelPlanner-agent-ui`, VPC: `TravelPlanner-agent-ui-vpc`, SGs: `TravelPlanner-agent-ui-alb-sg` / `TravelPlanner-agent-ui-ecs-sg`, TG: `TravelPlanner-agent-ui-tg`)
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 1.2 Create `deploy-streamlit-app/cdk/__init__.py` (empty) and `deploy-streamlit-app/docker_app/__init__.py` (empty)
    - _Requirements: 12.2_
  - [x] 1.3 Create `deploy-streamlit-app/cdk.json` with `"app": "python3 app.py"` and recommended CDK feature flags
    - _Requirements: 12.2_
  - [x] 1.4 Create `deploy-streamlit-app/requirements.txt` with `aws-cdk-lib>=2.160.0` and `constructs>=10.0.0`
    - _Requirements: 12.2_

- [x] 2. Implement Docker application modules
  - [x] 2.1 Create `deploy-streamlit-app/docker_app/cognito_client.py` with `get_authenticator(secret_id, region)` function that reads Cognito parameters from Secrets Manager and returns a `CognitoAuthenticator` instance
    - Retrieve `pool_id`, `app_client_id`, `app_client_secret` from the secret
    - Use `boto3` Secrets Manager client
    - _Requirements: 2.1, 2.2_
  - [x] 2.2 Create `deploy-streamlit-app/docker_app/agent_client.py` adapted from `streamlit_app/agent_client.py`
    - Read `TRAVEL_AGENT_URL` from environment variable
    - Implement `get_config_errors()` returning missing env var names
    - Implement `invoke(prompt)` sending SigV4-signed HTTP POST with service name `bedrock-agentcore`
    - Use `botocore.auth.SigV4Auth` and `httpx` for the request
    - Raise `RuntimeError` on non-200 or network errors
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  - [x] 2.3 Create `deploy-streamlit-app/docker_app/app.py` — Streamlit entry point
    - Initialize `CognitoAuthenticator` via `cognito_client.get_authenticator()` using config values
    - Call `authenticator.login()` and `st.stop()` if not authenticated
    - Check `agent_client.get_config_errors()` and show error + stop if missing config
    - Render sidebar with username display and logout button
    - Render chat interface with message history and input
    - On user input, call `agent_client.invoke(prompt)` and display response
    - Catch exceptions and display via `st.error()`
    - _Requirements: 2.3, 2.4, 2.5, 3.3, 3.4, 3.5_

- [x] 3. Create Docker container configuration
  - [x] 3.1 Create `deploy-streamlit-app/docker_app/Dockerfile` using `python:3.12` base image for `linux/amd64`, exposing port 8501, installing dependencies, and running `streamlit run app.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 3.2 Create `deploy-streamlit-app/docker_app/requirements.txt` with `boto3`, `httpx`, `streamlit`, and `streamlit-cognito-auth`
    - _Requirements: 4.3_

- [x] 4. Checkpoint — Verify Docker app structure
  - Ensure all files in `deploy-streamlit-app/docker_app/` are created with correct flat module structure (no `utils/` directory, no `docker-compose.yml`). Ask the user if questions arise.

- [x] 5. Implement CDK infrastructure stack
  - [x] 5.1 Create `deploy-streamlit-app/cdk/cdk_stack.py` — Cognito and Secrets Manager resources
    - Create Cognito User Pool and User Pool Client (with generated secret)
    - Store pool_id, app_client_id, app_client_secret in a Secrets Manager secret using the name from `Config.SECRETS_MANAGER_ID`
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 5.2 Add VPC and security group resources to `cdk_stack.py`
    - VPC with 2 AZs and 1 NAT gateway
    - ALB security group allowing inbound port 80
    - ECS security group allowing inbound port 8501 from ALB SG only
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 5.3 Add ECS Fargate cluster, task definition, and service to `cdk_stack.py`
    - ECS cluster with Fargate capacity providers
    - Fargate task definition (512 MiB memory, 256 CPU)
    - Build Docker image from `docker_app/` via `ContainerImage.from_asset('docker_app')`
    - Add container with port mapping 8501 and `TRAVEL_AGENT_URL` env var from CDK context (`self.node.try_get_context("travel_agent_url")`)
    - Fargate service in private subnets with ECS security group
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [x] 5.4 Add ALB, CloudFront, and listener configuration to `cdk_stack.py`
    - Internet-facing ALB in public subnets
    - ALB listener with custom header condition routing to ECS target group on port 8501
    - Default listener action returning HTTP 403
    - CloudFront distribution with ALB origin, custom header injection, HTTPS redirect, all methods allowed, caching disabled
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [x] 5.5 Add IAM policies and stack outputs to `cdk_stack.py`
    - Inline IAM policy granting `bedrock-agentcore:InvokeRuntime` on `*` to the task role
    - Grant Secrets Manager read access to the task role
    - CfnOutput for `CloudFrontDistributionURL` and `CognitoPoolId`
    - _Requirements: 10.1, 10.2, 11.1, 11.2_

- [x] 6. Create CDK entry point
  - [x] 6.1 Create `deploy-streamlit-app/app.py` — CDK app entry point that imports `Config` from `docker_app.config_file`, creates the CDK app, instantiates `CdkStack` with `Config.STACK_NAME` and `Config.DEPLOYMENT_REGION`
    - _Requirements: 12.2, 12.3_

- [x] 7. Checkpoint — Verify CDK synthesizes
  - Ensure all CDK files are in place and the stack structure is correct. Ask the user if questions arise.

- [x] 8. Update README with deployment instructions
  - [x] 8.1 Add a "Deploy Streamlit App" section to `README.md` with prerequisites (Docker, AWS CDK, Python, AWS credentials), step-by-step instructions for installing CDK dependencies, setting `TRAVEL_AGENT_URL` via CDK context, bootstrapping CDK, deploying the stack, and creating a Cognito user, plus how to access the app via CloudFront URL
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 9. Final checkpoint — Ensure all files are complete
  - Verify the full `deploy-streamlit-app/` directory structure matches the design. Ensure all tests pass, ask the user if questions arise.

## Notes

- No property-based tests — this is IaC + UI wiring, best validated with CDK assertions and manual testing
- The existing `streamlit_app/` directory is untouched; `deploy-streamlit-app/docker_app/` is a new containerized adaptation
- The CDK stack uses `bedrock-agentcore:InvokeRuntime` (not `bedrock:InvokeModel`) for the IAM policy
- `TRAVEL_AGENT_URL` is injected as a container env var from CDK context
- Docker image is built locally on Ubuntu Linux via `ContainerImage.from_asset('docker_app')`
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
