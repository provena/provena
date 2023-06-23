from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_apigateway as api_gw,
    aws_certificatemanager as aws_cm,
    aws_iam as iam,
    aws_secretsmanager as sm,
    Duration,
    RemovalPolicy
)
from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.utility.direct_secret_import import direct_import
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.component_constructs.data_registry import DataRegistry
from typing import Any, List


class LambdaDataStoreAPI(Construct):

    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 branch_name: str,
                 repo_string: str,
                 domain: str,
                 domain_base: str,
                 keycloak_endpoint: str,
                 keycloak_issuer: str,
                 handle_endpoint: str,
                 auth_api_endpoint: str,
                 registry_api_endpoint: str,
                 api_service_account_secret_arn: str,
                 oidc_service_account_secret_arn: str,
                 oidc_service_role_arn: str,
                 storage_bucket_arn: str,
                 allocator: DNSAllocator,
                 github_build_token_arn: str,
                 cert_arn: str,
                 extra_hash_dirs: List[str] = [],
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get bucket from arn
        bucket = s3.Bucket.from_bucket_arn(
            self, 'bucket', bucket_arn=storage_bucket_arn)

        # for deployment of docker container with authorized git dependencies
        # We need this secret at synthesis time so we need it as plain text in the environment
        oauth_token = direct_import(
            github_build_token_arn, Stack.of(self).region)

        # Create the function
        api_func = DockerImageLambda(
            self,
            'lambda',
            build_directory="../data-store-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string" : repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=extra_hash_dirs,
            # bump up size
            memory_size=2048
        )

        # Create a role which enables baseline read/write access to the bucket
        # and allows the lambda to assume it
        # for typing check that role is defined on function
        assert api_func.function.role
        bucket_assume_role = iam.Role(
            self,
            'api-bucket-role',
            assumed_by=api_func.function.role.grant_principal,
            description="Data API assumable role which enables delegation of access to storage bucket",

            # 12 hour max session duration (for now)
            max_session_duration=Duration.hours(12)
        )

        # Allow read/write to bucket
        bucket.grant_read_write(bucket_assume_role)

        # Get the secret
        service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='service-account-secret',
            secret_complete_arn=api_service_account_secret_arn
        )

        oidc_service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='oidc-service-account-secret',
            secret_complete_arn=oidc_service_account_secret_arn
        )

        # Grant read to data store api role
        service_secret.grant_read(api_func.function.role)
        oidc_service_secret.grant_read(api_func.function.role)

        # Environment

        # Make sure these parameters match deployment
        # requirements
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE" : domain_base,
            "KEYCLOAK_ISSUER": keycloak_issuer,
            "HANDLE_API_ENDPOINT": handle_endpoint,
            "AUTH_API_ENDPOINT": auth_api_endpoint,
            "REGISTRY_API_ENDPOINT": registry_api_endpoint,
            "S3_STORAGE_BUCKET_NAME": bucket.bucket_name,
            "STAGE": stage,
            "BUCKET_ROLE_ARN": bucket_assume_role.role_arn,
            "SERVICE_ACCOUNT_SECRET_ARN": api_service_account_secret_arn,
            "OIDC_SERVICE_ACCOUNT_SECRET_ARN": oidc_service_account_secret_arn,
            "OIDC_SERVICE_ROLE_ARN": oidc_service_role_arn,
        }

        for key, val in api_environment.items():
            api_func.function.add_environment(key, val)

        # Allow service to read/write to bucket
        bucket.grant_read_write(api_func.function.role)

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
            id="lambda-data-api-route",
            target=api,
            domain_prefix=domain,
            comment="Lambda Data API domain entry"
        )

        target_host = domain + "." + allocator.zone_domain_name

        # expose endpoint
        self.endpoint = f"https://{target_host}"
