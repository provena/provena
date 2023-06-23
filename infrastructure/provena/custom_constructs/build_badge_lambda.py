from aws_cdk import(
    aws_lambda as _lambda,
    aws_apigateway as api_gw,
    aws_codepipeline as code_pipeline,
    aws_iam as iam,
    aws_certificatemanager as aws_cm,
    CfnOutput
)

from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from typing import Any

class BuildBadgeLambda(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 domain: str,
                 stage: str,
                 cert_arn: str,
                 allocator: DNSAllocator,
                 built_pipeline: code_pipeline.Pipeline,
                 **kwargs: Any) -> None:

        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # Create function
        lambda_function = _lambda.Function(
            scope=self,
            id='func',
            code=_lambda.Code.from_asset(
                path="provena/lambda_utility/build_badge"
            ),
            handler="lambda_function.handler",
            runtime=_lambda.Runtime.PYTHON_3_9
        )

        # Setup api gw integration
        # retrieve certificate
        acm_cert = aws_cm.Certificate.from_certificate_arn(
            self, "api-cert", cert_arn
        )

        # Setup API endpoint - don't do anything else with it yet
        api = api_gw.LambdaRestApi(
            scope=self,
            id='api',
            handler=lambda_function,
            proxy=True,
            binary_media_types=["*/*"],
            domain_name=api_gw.DomainNameOptions(
                domain_name=f"{domain}.{allocator.zone_domain_name}",
                certificate=acm_cert
            )
        )

        # Setup dns route to hit this
        allocator.add_api_gateway_target(
            id=f"{stage}_{construct_id}_route",
            target=api,
            domain_prefix=domain,
            comment="API Gateway for build badge generation"
        )

        # Enable API access to required resources
        pipeline_arn = built_pipeline.pipeline_arn
        pipeline_name = built_pipeline.pipeline_name
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                # allow
                effect=iam.Effect.ALLOW,
                # listing and fetching
                actions=[
                    "codepipeline:GetPipelineExecution",
                    "codepipeline:GetPipelineState",
                    "codepipeline:ListPipelineExecutions"
                ],
                # for the specified pipeline
                resources=[pipeline_arn]
            )
        )
        # Add pipeline name env variable
        lambda_function.add_environment(
            key="PIPELINE_NAME",
            value=pipeline_name
        )

        # Output badge endpoint
        endpoint = f"https://{domain}.{allocator.zone_domain_name}"
        output = CfnOutput(
            scope=self,
            id='output',
            value=endpoint
        )
