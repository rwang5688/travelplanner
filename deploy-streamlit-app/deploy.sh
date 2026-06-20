#!/bin/bash
# Deploy the Streamlit Travel Planner UI to ECS Fargate
# Run from: ~/workshop/travelplanner/deploy-streamlit-app

set -euo pipefail

TRAVEL_AGENT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/travelplanner_TravelAgent-IWFLmB3nGT/invoke"

echo "Deploying TravelPlanner Streamlit app..."
echo "TRAVEL_AGENT_URL: ${TRAVEL_AGENT_URL}"

cdk deploy -c travel_agent_url="${TRAVEL_AGENT_URL}" --require-approval never

echo "Deploy complete."
