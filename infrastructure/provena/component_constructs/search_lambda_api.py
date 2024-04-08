from aws_cdk import (
    Stack,
    aws_certificatemanager as aws_cm,
    aws_apigateway as api_gw,
    RemovalPolicy,
    aws_secretsmanager as sm,
)
from constructs import Construct
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.utility.direct_secret_import import direct_import
from provena.config.config_class import APIGatewayRateLimitingSettings, SentryConfig
from typing import Any, List, Optional


class LambdaSearchAPI(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 branch_name: str,
                 repo_string: str,
                 domain: str,
                 domain_base: str,
                 keycloak_endpoint: str,
                 github_build_token_arn: str,
                 allocator: DNSAllocator,
                 cert_arn: str,
                 unqualified_search_domain: str,
                 registry_index: str,
                 global_index: str,
                 linearised_field_name: str,
                 api_rate_limiting: Optional[APIGatewayRateLimitingSettings],
                 git_commit_id: Optional[str],
                 sentry_config: SentryConfig,
                 feature_number: Optional[int],
                 extra_hash_dirs: List[str] = [],
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # for deployment of docker container with authorized git dependencies
        # We need this secret at synthesis time so we need it as plain text in the environment
        oauth_token = direct_import(
            github_build_token_arn, Stack.of(self).region)

        # Create the function
        api_func = DockerImageLambda(
            self,
            'lambda',
            build_directory="../search-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string": repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=extra_hash_dirs
        )
        
        assert api_func.function.role

        # Environment

        # Make sure these parameters match deployment
        # requirements
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE": domain_base,
            "STAGE": stage,
            "SEARCH_DOMAIN": unqualified_search_domain,
            "REGISTRY_INDEX": registry_index,
            "GLOBAL_INDEX": global_index,
            "LINEARISED_FIELD": linearised_field_name,
            "MONITORING_ENABLED": str(sentry_config.monitoring_enabled),
            "GIT_COMMIT_ID": git_commit_id,
            "SENTRY_DSN": sentry_config.sentry_dsn_back_end,
            "FEATURE_NUMBER": str(feature_number)
        }

        for key, val in api_environment.items():
            if val is not None:
                api_func.function.add_environment(key, val)

        # Setup api gw integration
        # retrieve certificate
        acm_cert = aws_cm.Certificate.from_certificate_arn(
            self, "api-cert", cert_arn
        )

        # Setup API gateway routing
        api = api_gw.LambdaRestApi(
            scope=self,
            id='apigw',
            handler=api_func.function,
            # Greedy proxy forwards all traffic at endpoint
            # to lambda
            proxy=True,
            domain_name=api_gw.DomainNameOptions(
                domain_name=f"{domain}.{allocator.zone_domain_name}",
                certificate=acm_cert
            ),
            deploy_options=api_gw.StageOptions(
                description="Search API Docker Lambda FastAPI API Gateway",
                throttling_burst_limit=api_rate_limiting.throttling_burst_limit if api_rate_limiting else None,
                throttling_rate_limit=api_rate_limiting.throttling_rate_limit if api_rate_limiting else None,
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="lambda-search-api-route",
            target=api,
            domain_prefix=domain,
            comment="Lambda Search API domain entry"
        )

        # Add rule to listener to hit this target group
        target_host = domain + "." + allocator.zone_domain_name

        # expose endpoint
        self.endpoint = f"https://{target_host}"
        self.function = api_func.function
