#!/bin/bash
# Deploy the Streamlit Travel Planner UI to ECS Fargate
# Run from: ~/workshop/travelplanner/deploy-streamlit-app

set -euo pipefail

TRAVEL_AGENT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A539307129890%3Aruntime%2Ftravelplanner_TravelAgent-IWFLmB3nGT/invocations"

echo "Deploying TravelPlanner Streamlit app..."
echo "TRAVEL_AGENT_URL: ${TRAVEL_AGENT_URL}"

cdk deploy -c travel_agent_url="${TRAVEL_AGENT_URL}" --require-approval never

echo "Deploy complete."
