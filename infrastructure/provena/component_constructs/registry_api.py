from aws_cdk import (
    Stack,
    aws_apigateway as api_gw,
    aws_certificatemanager as aws_cm,
    aws_secretsmanager as sm,
    Duration,
    RemovalPolicy,
    aws_iam as iam
)

from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.utility.direct_secret_import import direct_import
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.component_constructs.registry_table import RegistryTable, IdIndexTable
from typing import Any, List, Optional


REGISTRY_API_TIMEOUT = 60  # seconds


class RegistryAPI(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 branch_name: str,
                 repo_string: str,
                 domain: str,
                 domain_base: str,
                 keycloak_endpoint: str,
                 handle_endpoint: str,
                 auth_api_endpoint: str,
                 api_service_account_secret_arn: str,
                 allocator: DNSAllocator,
                 github_build_token_arn: str,
                 cert_arn: str,
                 registry_table: RegistryTable,
                 auth_table: IdIndexTable,
                 lock_table: IdIndexTable,
                 git_commit_id: Optional[str],
                 git_commit_url: Optional[str],
                 git_tag_name: Optional[str],
                 git_release_title: Optional[str],
                 git_release_url: Optional[str],
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
            build_directory="../registry-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string" : repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=extra_hash_dirs,
            timeout=Duration.seconds(REGISTRY_API_TIMEOUT)
        )

        # Create a role which enables baseline read/write access to the bucket
        # and allows the lambda to assume it
        # for typing check that role is defined on function
        assert api_func.function.role

        # Get the secret
        service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='service-account-secret',
            secret_complete_arn=api_service_account_secret_arn
        )


        # Environment

        # Make sure these parameters match deployment
        # requirements


        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE": domain_base,
            "HANDLE_API_ENDPOINT": handle_endpoint,
            "AUTH_API_ENDPOINT": auth_api_endpoint,
            "STAGE": stage,
            "REGISTRY_TABLE_NAME": registry_table.table_name,
            "AUTH_TABLE_NAME": auth_table.table_name,
            "LOCK_TABLE_NAME": lock_table.table_name,
            "SERVICE_ACCOUNT_SECRET_ARN": api_service_account_secret_arn,
            "GIT_COMMIT_ID": git_commit_id,
            "GIT_COMMIT_URL": git_commit_url,
            "GIT_TAG_NAME": git_tag_name,
            "GIT_RELEASE_TITLE": git_release_title,
            "GIT_RELEASE_URL": git_release_url,
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
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="lambda-registry-api-route",
            target=api,
            domain_prefix=domain,
            comment="Lambda Registry API domain entry"
        )

        target_host = domain + "." + allocator.zone_domain_name

        # expose endpoint
        self.endpoint = f"https://{target_host}"

        
        def grant_api_equivalent_permissions(grantee: iam.IGrantable) -> None:
            # let api r/w registry table
            registry_table.table.grant_read_write_data(grantee)
            # and auth/lock table
            auth_table.table.grant_read_write_data(grantee)
            lock_table.table.grant_read_write_data(grantee)

            # let api func act as service acc
            service_secret.grant_read(grantee)

        # grant permissions to registry api
        grant_api_equivalent_permissions(api_func.function)
        
        self.registry_api_environment = api_environment
        self.grant_api_equivalent_permissions = grant_api_equivalent_permissions
        self.add_to_environment = api_func.function.add_environment
