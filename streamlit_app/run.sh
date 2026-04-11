#!/usr/bin/env bash
# Launch the Streamlit Travel Planner app (Git Bash / Linux / macOS)
# Usage: bash streamlit_app/run.sh
#
# Requires AWS credentials in your environment (aws configure, SSO, etc.)

export TRAVEL_AGENT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A539307129890%3Aruntime%2Ftravelplanner_TravelAgent-IWFLmB3nGT/invocations"

streamlit run streamlit_app/app.py
