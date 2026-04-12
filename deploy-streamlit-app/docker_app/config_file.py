class Config:
    # Stack name
    # Change this value if you want to create a new instance of the stack
    STACK_NAME = "TravelPlanner"

    # Put your own custom value here to prevent ALB from accepting requests from
    # clients other than CloudFront. You can choose any random string.
    CUSTOM_HEADER_VALUE = "Xk9mTv3pQw7nRj2sLf8yBc4dAe6hUi1o"

    # ID of Secrets Manager containing cognito parameters
    # When you delete a secret, you cannot create another one immediately
    # with the same name. Change this value if you destroy your stack and need
    # to recreate it with the same STACK_NAME.
    SECRETS_MANAGER_ID = f"{STACK_NAME}ParamCognitoSecret12345"

    # AWS region in which you want to deploy the cdk stack
    DEPLOYMENT_REGION = "us-east-1"

    # Resource naming convention: STACK_NAME + "-agent-ui" suffix
    APP_NAME = f"{STACK_NAME}-agent-ui"

    # ALB name
    ALB_NAME = APP_NAME

    # ECS service name
    ECS_SERVICE_NAME = APP_NAME

    # VPC name
    VPC_NAME = f"{APP_NAME}-vpc"

    # Security group names
    ALB_SG_NAME = f"{APP_NAME}-alb-sg"
    ECS_SG_NAME = f"{APP_NAME}-ecs-sg"

    # Target group name
    TARGET_GROUP_NAME = f"{APP_NAME}-tg"
