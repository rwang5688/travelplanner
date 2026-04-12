"""Cognito authentication module.

Retrieves Cognito User Pool parameters from AWS Secrets Manager
and returns a configured CognitoAuthenticator instance for
Streamlit-based login/logout.
"""

import json

import boto3
from streamlit_cognito_auth import CognitoAuthenticator


def get_authenticator(secret_id: str, region: str) -> CognitoAuthenticator:
    """Get a CognitoAuthenticator by reading pool params from Secrets Manager.

    Args:
        secret_id: The Secrets Manager secret ID containing Cognito parameters.
        region: The AWS region where the secret is stored.

    Returns:
        A configured CognitoAuthenticator instance ready for login/logout.
    """
    secretsmanager_client = boto3.client("secretsmanager", region_name=region)
    response = secretsmanager_client.get_secret_value(SecretId=secret_id)
    secret = json.loads(response["SecretString"])

    return CognitoAuthenticator(
        pool_id=secret["pool_id"],
        app_client_id=secret["app_client_id"],
        app_client_secret=secret["app_client_secret"],
    )
