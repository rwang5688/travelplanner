from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_secretsmanager as secretsmanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    SecretValue,
    CfnOutput,
)
from constructs import Construct
from docker_app.config_file import Config

CUSTOM_HEADER_NAME = "X-Custom-Header"


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define prefix that will be used in some resource names
        prefix = Config.STACK_NAME

        # ---------------------------------------------------------------
        # Task 5.1: Cognito and Secrets Manager
        # ---------------------------------------------------------------

        # Create Cognito user pool
        user_pool = cognito.UserPool(self, f"{prefix}UserPool")

        # Create Cognito client with generated secret
        user_pool_client = cognito.UserPoolClient(
            self,
            f"{prefix}UserPoolClient",
            user_pool=user_pool,
            generate_secret=True,
        )

        # Store Cognito parameters in Secrets Manager
        secret = secretsmanager.Secret(
            self,
            f"{prefix}ParamCognitoSecret",
            secret_object_value={
                "pool_id": SecretValue.unsafe_plain_text(user_pool.user_pool_id),
                "app_client_id": SecretValue.unsafe_plain_text(
                    user_pool_client.user_pool_client_id
                ),
                "app_client_secret": user_pool_client.user_pool_client_secret,
            },
            secret_name=Config.SECRETS_MANAGER_ID,
        )

        # ---------------------------------------------------------------
        # Task 5.2: VPC and Security Groups
        # ---------------------------------------------------------------

        # VPC for ALB and ECS cluster
        vpc = ec2.Vpc(
            self,
            f"{prefix}AppVpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            vpc_name=Config.VPC_NAME,
            nat_gateways=1,
        )

        alb_security_group = ec2.SecurityGroup(
            self,
            f"{prefix}SecurityGroupALB",
            vpc=vpc,
            security_group_name=Config.ALB_SG_NAME,
        )

        ecs_security_group = ec2.SecurityGroup(
            self,
            f"{prefix}SecurityGroupECS",
            vpc=vpc,
            security_group_name=Config.ECS_SG_NAME,
        )

        ecs_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(8501),
            description="ALB traffic",
        )

        # ---------------------------------------------------------------
        # Task 5.3: ECS Fargate
        # ---------------------------------------------------------------

        # ECS cluster
        cluster = ecs.Cluster(
            self,
            f"{prefix}Cluster",
            enable_fargate_capacity_providers=True,
            vpc=vpc,
        )

        # Fargate task definition (ARM64 for Graviton-based builds)
        fargate_task_definition = ecs.FargateTaskDefinition(
            self,
            f"{prefix}WebappTaskDef",
            memory_limit_mib=512,
            cpu=256,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )

        # Build Docker image from docker_app/
        image = ecs.ContainerImage.from_asset("docker_app")

        # Add container with port mapping and TRAVEL_AGENT_URL env var
        fargate_task_definition.add_container(
            f"{prefix}WebContainer",
            image=image,
            port_mappings=[
                ecs.PortMapping(
                    container_port=8501,
                    protocol=ecs.Protocol.TCP,
                )
            ],
            environment={
                "TRAVEL_AGENT_URL": self.node.try_get_context("travel_agent_url") or "",
            },
            logging=ecs.LogDrivers.aws_logs(stream_prefix="WebContainerLogs"),
        )

        # Fargate service in private subnets
        service = ecs.FargateService(
            self,
            f"{prefix}ECSService",
            cluster=cluster,
            task_definition=fargate_task_definition,
            service_name=Config.ECS_SERVICE_NAME,
            security_groups=[ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # ---------------------------------------------------------------
        # Task 5.4: ALB and CloudFront
        # ---------------------------------------------------------------

        # Internet-facing ALB in public subnets
        alb = elbv2.ApplicationLoadBalancer(
            self,
            f"{prefix}Alb",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name=Config.ALB_NAME,
            security_group=alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        # CloudFront distribution with ALB origin
        origin = origins.LoadBalancerV2Origin(
            alb,
            custom_headers={CUSTOM_HEADER_NAME: Config.CUSTOM_HEADER_VALUE},
            origin_shield_enabled=False,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        )

        cloudfront_distribution = cloudfront.Distribution(
            self,
            f"{prefix}CfDist",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
            ),
        )

        # ALB Listener on port 80
        http_listener = alb.add_listener(
            f"{prefix}HttpListener",
            port=80,
            open=True,
        )

        # Route requests with custom header to ECS target group
        http_listener.add_targets(
            f"{prefix}TargetGroup",
            target_group_name=Config.TARGET_GROUP_NAME,
            port=8501,
            priority=1,
            conditions=[
                elbv2.ListenerCondition.http_header(
                    CUSTOM_HEADER_NAME,
                    [Config.CUSTOM_HEADER_VALUE],
                )
            ],
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
        )

        # Default action: deny requests without custom header
        http_listener.add_action(
            "default-action",
            action=elbv2.ListenerAction.fixed_response(
                status_code=403,
                content_type="text/plain",
                message_body="Access denied",
            ),
        )

        # ---------------------------------------------------------------
        # Task 5.5: IAM Policies and Outputs
        # ---------------------------------------------------------------

        # Grant bedrock-agentcore:InvokeRuntime to the task role
        agentcore_policy = iam.Policy(
            self,
            f"{prefix}AgentCorePolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["bedrock-agentcore:InvokeRuntime"],
                    resources=["*"],
                )
            ],
        )
        task_role = fargate_task_definition.task_role
        task_role.attach_inline_policy(agentcore_policy)

        # Grant Secrets Manager read access to the task role
        secret.grant_read(task_role)

        # Stack outputs
        CfnOutput(
            self,
            "CloudFrontDistributionURL",
            value=cloudfront_distribution.domain_name,
        )
        CfnOutput(
            self,
            "CognitoPoolId",
            value=user_pool.user_pool_id,
        )
