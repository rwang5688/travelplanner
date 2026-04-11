# Launch the Streamlit Travel Planner app (PowerShell)
# Usage: .\streamlit_app\run.ps1
#
# Requires AWS credentials in your environment (aws configure, SSO, etc.)

$env:TRAVEL_AGENT_URL = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A539307129890%3Aruntime%2Ftravelplanner_TravelAgent-IWFLmB3nGT/invocations"

streamlit run streamlit_app/app.py
