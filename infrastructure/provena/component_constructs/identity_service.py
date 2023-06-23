from aws_cdk import (
    Duration,
    aws_apigateway as api_gw,
    aws_certificatemanager as aws_cm,
    aws_secretsmanager as sm,
    Stack,
    RemovalPolicy
)
from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.utility.direct_secret_import import direct_import
from typing import Any, List

IDENTITY_API_TIMEOUT = 60  # seconds


class IdentityService(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 domain_base: str,
                 extra_hash_dirs: List[str],
                 handle_endpoint: str,
                 handle_secret_arn: str,
                 branch_name: str,
                 repo_string: str,
                 keycloak_auth_endpoint: str,
                 cert_arn: str,
                 domain: str,
                 build_github_token_arn: str,
                 allocator: DNSAllocator,
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # for deployment of lambda bundles - need access into repo
        # We need this secret at synthesis time so we need it as plain text in the environment
        # Unfortuantely CDK doesn't resolve the token in this case so we have to use the boto sdk to
        # pull the token
        oauth_token = direct_import(
            build_github_token_arn, Stack.of(self).region)

        # Create the function
        api_func = DockerImageLambda(
            self,
            'lambda',
            build_directory="../identity-service",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string" : repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=extra_hash_dirs,
            timeout=Duration.seconds(IDENTITY_API_TIMEOUT)
        )
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_auth_endpoint,
            "DOMAIN_BASE" : domain_base,
            "STAGE": stage,
            "HANDLE_SERVICE_CREDS_ARN": handle_secret_arn,
            "HANDLE_SERVICE_ENDPOINT": handle_endpoint
        }

        # Get the secret and grant read
        service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='handle-creds-secret',
            secret_complete_arn=handle_secret_arn
        )

        assert api_func.function.role
        service_secret.grant_read(api_func.function.role)

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
            id="lambda-identity-service-route",
            target=api,
            domain_prefix=domain,
            comment="Lambda Identity Service API domain entry"
        )

        target_host = domain + "." + allocator.zone_domain_name

        # expose endpoint
        self.handle_endpoint = f"https://{target_host}"
