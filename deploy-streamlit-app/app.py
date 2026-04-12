#!/usr/bin/env python3
"""CDK app entry point for the Travel Planner Streamlit deployment."""

import aws_cdk as cdk

from cdk.cdk_stack import CdkStack
from docker_app.config_file import Config

app = cdk.App()
CdkStack(
    app,
    Config.STACK_NAME,
    env=cdk.Environment(region=Config.DEPLOYMENT_REGION),
)
app.synth()
