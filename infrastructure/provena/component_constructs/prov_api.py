from aws_cdk import (
    Stack,
    aws_apigateway as api_gw,
    aws_certificatemanager as aws_cm,
    aws_secretsmanager as sm,
    Duration,
    RemovalPolicy
)

from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.utility.direct_secret_import import direct_import
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from typing import Any, Optional, List

# increased over default 20 seconds because of chained cold starts and neo4j
# initialisation
DEFAULT_PROV_API_TIMEOUT = Duration.seconds(35)


class ProvAPI(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 branch_name: str,
                 repo_string: str,
                 domain: str,
                 domain_base: str,
                 keycloak_endpoint: str,
                 service_account_secret_arn: str,
                 allocator: DNSAllocator,
                 github_build_token_arn: str,
                 neo4j_host: str,
                 neo4j_port: str,
                 neo4j_auth_arn: str,
                 registry_api_endpoint: str,
                 data_store_api_endpoint: str,
                 cert_arn: str,
                 function_timeout: Duration = DEFAULT_PROV_API_TIMEOUT,
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
            build_directory="../prov-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string" : repo_string,
                "branch_name": branch_name
            },
            timeout=function_timeout,
            # bump up to 2GB ram for prov function
            memory_size=3096,
            extra_hash_dirs=extra_hash_dirs
        )

        # Create a role which enables baseline read/write access to the bucket
        # and allows the lambda to assume it
        # for typing check that role is defined on function
        assert api_func.function.role

        # Get the secret
        service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='service-account-secret',
            secret_complete_arn=service_account_secret_arn
        )

        # Grant read to data store api role
        service_secret.grant_read(api_func.function.role)

        # Get the secret
        neo4j_auth_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='neo4j-secret',
            secret_complete_arn=neo4j_auth_arn
        )

        # Grant read to data store api role
        neo4j_auth_secret.grant_read(api_func.function.role)

        # Environment

        # Make sure these parameters match deployment
        # requirements
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE" : domain_base,
            "STAGE": stage,
            "SERVICE_ACCOUNT_SECRET_ARN": service_account_secret_arn,
            "NEO4J_HOST": neo4j_host,
            "NEO4J_PORT": neo4j_port,
            "NEO4J_AUTH_ARN": neo4j_auth_arn,
            "REGISTRY_API_ENDPOINT": registry_api_endpoint,
            "DATA_STORE_API_ENDPOINT": data_store_api_endpoint
        }

        for key, val in api_environment.items():
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
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="lambda-prov-api-route",
            target=api,
            domain_prefix=domain,
            comment="Lambda Prov API domain entry"
        )

        target_host = domain + "." + allocator.zone_domain_name

        # expose endpoint and function
        self.endpoint = f"https://{target_host}"
        self.function = api_func.function
