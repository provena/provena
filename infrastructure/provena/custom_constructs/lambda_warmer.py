from aws_cdk import (
    Duration,
    aws_certificatemanager as aws_cm,
    aws_apigateway as api_gw,
    RemovalPolicy
)

from constructs import Construct
from dataclasses import dataclass
from typing import Any, Optional, Dict
from provena.custom_constructs.docker_bundled_lambda import DockerizedLambda
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.config.config_class import APIGatewayRateLimitingSettings


@dataclass
class WarmerEndpoints:
    DATA_STORE_API_ENDPOINT: Optional[str]
    REGISTRY_API_ENDPOINT: Optional[str]
    PROV_API_ENDPOINT: Optional[str]
    HANDLE_API_ENDPOINT: Optional[str]
    AUTH_API_ENDPOINT: Optional[str]
    SEARCH_API_ENDPOINT: Optional[str]
    JOB_API_ENDPOINT: Optional[str]


def warmer_endpoints_to_env_map(endpoints: WarmerEndpoints) -> Dict[str, str]:
    env = {}
    if endpoints.DATA_STORE_API_ENDPOINT:
        env["DATA_STORE_API_ENDPOINT"] = endpoints.DATA_STORE_API_ENDPOINT
    if endpoints.REGISTRY_API_ENDPOINT:
        env["REGISTRY_API_ENDPOINT"] = endpoints.REGISTRY_API_ENDPOINT
    if endpoints.PROV_API_ENDPOINT:
        env["PROV_API_ENDPOINT"] = endpoints.PROV_API_ENDPOINT
    if endpoints.HANDLE_API_ENDPOINT:
        env["HANDLE_API_ENDPOINT"] = endpoints.HANDLE_API_ENDPOINT
    if endpoints.AUTH_API_ENDPOINT:
        env["AUTH_API_ENDPOINT"] = endpoints.AUTH_API_ENDPOINT
    if endpoints.SEARCH_API_ENDPOINT:
        env["SEARCH_API_ENDPOINT"] = endpoints.SEARCH_API_ENDPOINT
    if endpoints.JOB_API_ENDPOINT:
        env["JOB_API_ENDPOINT"] = endpoints.JOB_API_ENDPOINT
    return env


class LambdaWarmer(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            sub_domain: str,
            allocator: DNSAllocator,
            endpoints: WarmerEndpoints,
            api_rate_limiting: Optional[APIGatewayRateLimitingSettings],
            cert_arn: str,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        warmer_lambda = DockerizedLambda(
            scope=self,
            id="warmer_lambda",
            path="provena/lambda_utility/api_warmer",
            handler="lambda_function.handler",
            timeout=Duration.seconds(60),
        )
        warmer_function = warmer_lambda.function

        env = warmer_endpoints_to_env_map(endpoints=endpoints)
        for k, v in env.items():
            warmer_function.add_environment(k, v)

        # retrieve certificate
        acm_cert = aws_cm.Certificate.from_certificate_arn(
            self, "api-cert", cert_arn
        )

        # Setup API gateway routing
        api = api_gw.LambdaRestApi(
            scope=self,
            id='warmer_api',
            handler=warmer_function,
            # Greedy proxy forwards all traffic at endpoint
            # to lambda
            proxy=True,
            domain_name=api_gw.DomainNameOptions(
                domain_name=f"{sub_domain}.{allocator.root_domain}",
                certificate=acm_cert
            ),
            deploy_options=api_gw.StageOptions(
                description="Warmer Lambda FastAPI API Gateway",
                throttling_burst_limit=api_rate_limiting.throttling_burst_limit if api_rate_limiting else None,
                throttling_rate_limit=api_rate_limiting.throttling_rate_limit if api_rate_limiting else None,
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="warmer_api_route",
            target=api,
            domain=sub_domain,
            comment="Warmer API domain entry"
        )

        # Full name of api
        self.endpoint = f"https://{sub_domain}.{allocator.root_domain}"
