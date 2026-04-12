# AgentCore Project

This project was created with the [AgentCore CLI](https://github.com/aws/agentcore-cli).

## Project Structure

```
.
my-project/
├── agentcore/
│   ├── .env.local          # API keys (gitignored)
│   ├── agentcore.json      # Resource specifications
│   ├── aws-targets.json    # Deployment targets
│   └── cdk/                # CDK infrastructure
├── app/                    # Application code
```

## Getting Started

### Prerequisites

- **Node.js** 20.x or later
- **uv** for Python agents ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Development

Run your agent locally:

```bash
agentcore dev
```

### Deployment

Deploy to AWS:

```bash
agentcore deploy
```

Or use CDK directly:

```bash
cd agentcore/cdk
npx cdk deploy
```

## Configuration

Edit the JSON files in `agentcore/` to configure your agents, memory, and credentials. See `agentcore/.llm-context/` for
type definitions and validation constraints.

The project uses a **flat resource model** where agents, memories, and credentials are top-level arrays in
`agentcore.json`.

## Commands

| Command              | Description                                     |
| -------------------- | ----------------------------------------------- |
| `agentcore create`   | Create a new AgentCore project                  |
| `agentcore add`      | Add resources (agent, memory, identity, target) |
| `agentcore remove`   | Remove resources                                |
| `agentcore dev`      | Run agent locally                               |
| `agentcore deploy`   | Deploy to AWS                                   |
| `agentcore status`   | Show deployment status                          |
| `agentcore invoke`   | Invoke agent (local or deployed)                |
| `agentcore package`  | Package agent artifacts                         |
| `agentcore validate` | Validate configuration                          |
| `agentcore update`   | Check for CLI updates                           |

### Agent Types

- **Template agents**: Created from framework templates (Strands, LangChain_LangGraph, GoogleADK, OpenAIAgents)
- **BYO agents**: Bring your own code with `agentcore add agent --type byo`

## Documentation

- [AgentCore CLI Documentation](https://github.com/aws/agentcore-cli)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)

## Deploy Streamlit App (ECS Fargate)

The `deploy-streamlit-app/` directory contains a containerized version of the Travel Planner Streamlit app with Cognito user authentication, deployed on ECS Fargate behind an ALB and CloudFront.

### Architecture

- **CloudFront** → **ALB** (with custom header validation) → **ECS Fargate** (Streamlit container)
- **Cognito User Pool** for user authentication (parameters stored in Secrets Manager)
- Container invokes the TravelAgent runtime via SigV4-signed HTTP POST

### Prerequisites

- Python 3.12+
- Docker (running)
- AWS CDK (`npm install -g aws-cdk`)
- AWS CLI configured with credentials
- TravelAgent deployed via `agentcore deploy` (you need the runtime URL)

### Deploy

1. Set the TravelAgent runtime URL. Run `agentcore status` to find the TravelAgent URL, then add it to your `~/.bashrc`:

```bash
export TRAVEL_AGENT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A<ACCOUNT_ID>%3Aruntime%2Ftravelplanner_TravelAgent-<RUNTIME_ID>/invocations"
```

Then source it to pick up the variable in your current shell:

```bash
source ~/.bashrc
```

2. Navigate to the deploy directory:

```bash
cd deploy-streamlit-app
```

3. Install CDK dependencies:

```bash
pip install -r requirements.txt
```

4. Bootstrap CDK (first time only):

```bash
cdk bootstrap
```

5. Deploy the stack:

```bash
cdk deploy -c travel_agent_url="$TRAVEL_AGENT_URL"
```

The deployment takes 5–10 minutes. CDK will build the Docker image locally and push it to ECR.

6. Note the outputs:
   - `CloudFrontDistributionURL` — the app URL
   - `CognitoPoolId` — the Cognito User Pool ID

7. Create a user in the Cognito User Pool via the AWS Console.

8. Open the CloudFront URL in your browser and log in with the Cognito user.

### Configuration

Edit `deploy-streamlit-app/docker_app/config_file.py` to change:
- `STACK_NAME` — CloudFormation stack name (default: `TravelPlanner`)
- `CUSTOM_HEADER_VALUE` — random string for ALB-CloudFront origin validation
- `DEPLOYMENT_REGION` — AWS region (default: `us-east-1`)

### Tear Down

```bash
cd deploy-streamlit-app
cdk destroy
```
