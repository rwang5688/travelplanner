# Requirements Document

## Introduction

This feature creates a production-ready deployment of the existing Travel Planner Streamlit application as a containerized service on AWS ECS Fargate. The deployment adds Cognito-based user authentication, packages the app in a Docker container, and provisions all required AWS infrastructure via CDK — including VPC, ECS cluster, ALB, CloudFront distribution, and IAM policies. The result is a `deploy-streamlit-app/` directory containing both the Docker application source and CDK infrastructure code, plus deployment instructions in the project README.

## Glossary

- **CDK_Stack**: The AWS CDK stack that provisions all infrastructure resources for the containerized Streamlit deployment
- **Docker_App**: The containerized version of the Streamlit application, located in `deploy-streamlit-app/docker_app/`
- **Cognito_Client**: The authentication module (`cognito_client.py`) that retrieves Cognito parameters from Secrets Manager and provides login/logout functionality via `streamlit-cognito-auth`
- **Agent_Client**: The HTTP client module (`agent_client.py`) that sends SigV4-signed requests to the TravelAgent runtime on AgentCore
- **Config_Module**: The Python configuration module (`config_file.py`) that defines stack name, Secrets Manager ID, deployment region, and custom header value
- **ALB**: The Application Load Balancer that routes traffic from CloudFront to the ECS Fargate service
- **CloudFront_Distribution**: The CloudFront distribution that serves as the public HTTPS entry point, forwarding requests to the ALB with a custom header for origin validation
- **ECS_Service**: The ECS Fargate service running the containerized Streamlit application
- **Secrets_Manager_Secret**: The AWS Secrets Manager secret storing Cognito User Pool parameters (pool ID, client ID, client secret)

## Requirements

### Requirement 1: Docker Application Structure

**User Story:** As a developer, I want the containerized app to follow a well-defined directory structure, so that the Docker build and CDK deployment work correctly.

#### Acceptance Criteria

1. THE Docker_App SHALL contain the following files: `app.py` (Streamlit entry point), `cognito_client.py` (Cognito authentication), `agent_client.py` (TravelAgent invocation), `config_file.py` (configuration), `Dockerfile`, and `requirements.txt`
2. THE Docker_App SHALL be located at `deploy-streamlit-app/docker_app/` relative to the project root

### Requirement 2: Cognito Authentication Module

**User Story:** As a developer, I want Cognito authentication logic isolated in its own module, so that auth concerns are separated from the UI and agent invocation logic.

#### Acceptance Criteria

1. THE Cognito_Client SHALL retrieve Cognito User Pool parameters (pool ID, client ID, client secret) from the Secrets_Manager_Secret using the secret ID and region defined in the Config_Module
2. THE Cognito_Client SHALL provide a `get_authenticator()` function that returns a configured `CognitoAuthenticator` instance
3. WHEN a user accesses the application, THE app.py entry point SHALL use the Cognito_Client to present a login screen before granting access to the chat interface
4. WHEN a user is not authenticated, THE app.py entry point SHALL stop rendering the page and display only the login form
5. WHEN a user clicks the logout button, THE Cognito_Client authenticator SHALL end the user session and return to the login screen

### Requirement 3: TravelAgent Integration in Container

**User Story:** As a developer, I want the containerized app to communicate with the TravelAgent runtime on AgentCore, so that users can interact with the travel planner through the deployed UI.

#### Acceptance Criteria

1. THE Agent_Client SHALL send SigV4-signed HTTP POST requests to the TravelAgent runtime URL
2. THE Agent_Client SHALL read the TravelAgent endpoint from the `TRAVEL_AGENT_URL` environment variable
3. WHEN a user submits a chat prompt, THE Docker_App SHALL send the prompt to the TravelAgent via the Agent_Client and display the response in the chat interface
4. IF the Agent_Client receives a non-200 HTTP response, THEN THE Docker_App SHALL display an error message to the user
5. IF the `TRAVEL_AGENT_URL` environment variable is missing, THEN THE Docker_App SHALL display a configuration error and stop rendering the chat interface

### Requirement 4: Docker Container Configuration

**User Story:** As a developer, I want a properly configured Docker container, so that the Streamlit app runs reliably in ECS Fargate.

#### Acceptance Criteria

1. THE Docker_App SHALL use a Python 3.12 base image built for the `linux/amd64` platform
2. THE Docker_App SHALL expose port 8501 for the Streamlit server
3. THE Docker_App SHALL install dependencies from `requirements.txt` including `streamlit`, `boto3`, `httpx`, and `streamlit-cognito-auth`
4. THE Docker_App SHALL support local testing by building and running the Docker image directly with `docker build` and `docker run`

### Requirement 5: Application Configuration Module

**User Story:** As a developer, I want a centralized configuration module, so that stack name, region, secrets, and security values are defined in one place.

#### Acceptance Criteria

1. THE Config_Module SHALL define the following configuration values: stack name, custom header value for ALB-CloudFront validation, Secrets Manager secret ID, and deployment region
2. THE Config_Module SHALL derive the Secrets Manager secret ID from the stack name to maintain naming consistency
3. THE Config_Module SHALL be importable by both the Docker_App application code and the CDK_Stack infrastructure code

### Requirement 6: CDK Infrastructure — Cognito and Secrets

**User Story:** As a developer, I want the CDK stack to provision Cognito resources, so that user authentication is fully automated during deployment.

#### Acceptance Criteria

1. THE CDK_Stack SHALL create a Cognito User Pool for user authentication
2. THE CDK_Stack SHALL create a Cognito User Pool Client with a generated client secret
3. THE CDK_Stack SHALL store the Cognito pool ID, client ID, and client secret in a Secrets_Manager_Secret using the secret name defined in the Config_Module

### Requirement 7: CDK Infrastructure — Networking

**User Story:** As a developer, I want the CDK stack to provision networking resources, so that the ECS service is securely accessible via the internet.

#### Acceptance Criteria

1. THE CDK_Stack SHALL create a VPC with 2 Availability Zones and 1 NAT gateway
2. THE CDK_Stack SHALL create an ALB security group that allows inbound HTTP traffic on port 80
3. THE CDK_Stack SHALL create an ECS security group that allows inbound traffic only from the ALB security group on port 8501
4. THE CDK_Stack SHALL place the ALB in public subnets and the ECS_Service in private subnets with egress

### Requirement 8: CDK Infrastructure — ECS Fargate

**User Story:** As a developer, I want the CDK stack to deploy the containerized app on ECS Fargate, so that the application runs as a managed container service.

#### Acceptance Criteria

1. THE CDK_Stack SHALL create an ECS Fargate cluster with Fargate capacity providers enabled
2. THE CDK_Stack SHALL define a Fargate task definition with 512 MiB memory and 256 CPU units
3. THE CDK_Stack SHALL build the Docker image from the `docker_app/` directory and add it as a container to the task definition with port mapping on 8501
4. THE CDK_Stack SHALL create a Fargate service running the task definition in private subnets with the ECS security group
5. THE CDK_Stack SHALL pass the `TRAVEL_AGENT_URL` environment variable to the container from CDK context or configuration

### Requirement 9: CDK Infrastructure — ALB and CloudFront

**User Story:** As a developer, I want the CDK stack to provision an ALB and CloudFront distribution, so that the application is accessible over HTTPS with origin validation.

#### Acceptance Criteria

1. THE CDK_Stack SHALL create an internet-facing ALB in public subnets
2. THE CDK_Stack SHALL configure the ALB listener to route requests to the ECS_Service only when the request contains a custom header matching the value defined in the Config_Module
3. THE CDK_Stack SHALL configure the ALB listener to return HTTP 403 for requests that do not contain the custom header
4. THE CDK_Stack SHALL create a CloudFront_Distribution that forwards requests to the ALB origin with the custom header injected automatically
5. THE CDK_Stack SHALL configure the CloudFront_Distribution to redirect HTTP to HTTPS, allow all HTTP methods, disable caching, and forward all viewer headers

### Requirement 10: CDK Infrastructure — IAM Policies

**User Story:** As a developer, I want the CDK stack to grant appropriate IAM permissions, so that the container can invoke the TravelAgent and read Cognito secrets.

#### Acceptance Criteria

1. THE CDK_Stack SHALL attach an inline IAM policy to the Fargate task role granting `bedrock-agentcore:InvokeRuntime` on all resources
2. THE CDK_Stack SHALL grant the Fargate task role read access to the Secrets_Manager_Secret

### Requirement 11: CDK Stack Outputs

**User Story:** As a developer, I want the CDK stack to output key resource identifiers, so that I can easily find the deployment URL and Cognito pool ID after deployment.

#### Acceptance Criteria

1. THE CDK_Stack SHALL output the CloudFront_Distribution domain name as a CloudFormation output named `CloudFrontDistributionURL`
2. THE CDK_Stack SHALL output the Cognito User Pool ID as a CloudFormation output named `CognitoPoolId`

### Requirement 12: CDK Project Structure

**User Story:** As a developer, I want the CDK project to follow standard conventions, so that I can deploy using familiar CDK commands.

#### Acceptance Criteria

1. THE CDK_Stack project SHALL be located at `deploy-streamlit-app/` relative to the project root
2. THE CDK_Stack project SHALL contain `app.py` (CDK entry point), `cdk.json` (CDK configuration), `requirements.txt` (with `aws-cdk-lib` dependency), and a `cdk/` directory with `__init__.py` and `cdk_stack.py`
3. THE CDK_Stack entry point (`app.py`) SHALL import the Config_Module from `docker_app/` and use the configured deployment region

### Requirement 13: README Deployment Instructions

**User Story:** As a developer, I want deployment instructions in the README, so that I can build and deploy the containerized Streamlit app without guessing the steps.

#### Acceptance Criteria

1. WHEN the feature is complete, THE README.md SHALL contain a new section documenting how to deploy the containerized Streamlit application
2. THE README.md deployment section SHALL include prerequisites (Docker, AWS CDK, Python, AWS credentials)
3. THE README.md deployment section SHALL include step-by-step instructions for installing CDK dependencies, setting the `TRAVEL_AGENT_URL`, bootstrapping CDK, deploying the stack, and creating a Cognito user
4. THE README.md deployment section SHALL document how to access the deployed application via the CloudFront URL
