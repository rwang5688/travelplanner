"""HTTP client for communicating with the TravelAgent runtime on AgentCore.

Reads configuration from environment variables and sends prompts to the
TravelAgent runtime via SigV4-signed HTTP POST requests using boto3.
"""

import json
import os

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

TRAVEL_AGENT_URL = os.environ.get("TRAVEL_AGENT_URL", "")

_REQUIRED_VARS = [
    "TRAVEL_AGENT_URL",
]


def get_config_errors() -> list[str]:
    """Return list of missing required environment variable names."""
    missing = []
    if not TRAVEL_AGENT_URL:
        missing.append("TRAVEL_AGENT_URL")
    return missing


def invoke(prompt: str) -> str:
    """Send prompt to TravelAgent and return the response text.

    Signs the request with SigV4 using the caller's AWS credentials,
    sends an HTTP POST to TRAVEL_AGENT_URL with JSON body {"prompt": prompt},
    and returns the "response" field from the JSON reply.

    Raises RuntimeError on non-200 status or network errors.
    """
    import httpx

    body = json.dumps({"prompt": prompt})

    # Build and sign the request with SigV4
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name or "us-east-1"

    aws_request = AWSRequest(
        method="POST",
        url=TRAVEL_AGENT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
    )
    SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(aws_request)

    try:
        resp = httpx.post(
            TRAVEL_AGENT_URL,
            content=body,
            headers=dict(aws_request.headers),
            timeout=120.0,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Agent request failed: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"Agent call failed ({resp.status_code}): {resp.text}"
        )

    return resp.json()["response"]
