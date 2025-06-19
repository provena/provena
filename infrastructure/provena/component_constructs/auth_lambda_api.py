from aws_cdk import (
    Stack,
    aws_secretsmanager as sm,
    aws_certificatemanager as aws_cm,
    aws_apigateway as api_gw,
    aws_lambda as _lambda,
    RemovalPolicy,
)
from constructs import Construct
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.utility.direct_secret_import import direct_import
from provena.custom_constructs.access_request_table import AccessRequestTable
from provena.custom_constructs.user_groups_table import UserGroupsTable
from provena.custom_constructs.username_person_link_table import UsernamePersonLinkTable
from provena.config.config_class import APIGatewayRateLimitingSettings, SentryConfig
from typing import Any, List, Optional, cast


class LambdaAuthApi(Construct):

    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 branch_name: str,
                 repo_string: str,
                 domain: str,
                 domain_base: str,
                 access_alerts_email_address: str,
                 registry_api_endpoint: str,
                 keycloak_endpoint: str,
                 api_service_account_secret_arn: str,
                 github_build_token_arn: str,
                 allocator: DNSAllocator,
                 cert_arn: str,
                 request_table_pitr: bool,
                 user_groups_table_pitr: bool,
                 api_rate_limiting: Optional[APIGatewayRateLimitingSettings],
                 request_table_removal_policy: RemovalPolicy,
                 groups_table_removal_policy: RemovalPolicy,
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
            build_directory="../auth-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string": repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=extra_hash_dirs
        )

        # Create the access request recording table
        access_request_table = AccessRequestTable(
            scope=self,
            construct_id="request-table",
            enable_pitr=request_table_pitr,
            removal_policy=request_table_removal_policy
        )

        # Grant read/write to lambda function
        assert api_func.function.role
        access_request_table.table.grant_read_write_data(
            api_func.function.role)

        # Create the groups table
        user_groups_table = UserGroupsTable(
            scope=self,
            construct_id="groups-table",
            enable_pitr=user_groups_table_pitr,
            removal_policy=groups_table_removal_policy
        )

        # Grant read/write to lambda function
        user_groups_table.table.grant_read_write_data(
            api_func.function.role)

        # Create the username/person link tabler
        username_person_link_table = UsernamePersonLinkTable(
            scope=self,
            id="username-person-link-table",
            enable_pitr=user_groups_table_pitr,
            removal_policy=groups_table_removal_policy
        )

        # Grant read/write to lambda function
        username_person_link_table.table.grant_read_write_data(
            api_func.function.role)

        # Environment

        # Make sure these parameters match deployment
        # requirements
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE": domain_base,
            "STAGE": stage,
            "REGISTRY_API_ENDPOINT": registry_api_endpoint,
            "ACCESS_REQUEST_TABLE_NAME": access_request_table.table.table_name,
            "USER_GROUPS_TABLE_NAME": user_groups_table.table.table_name,
            "SERVICE_ACCOUNT_SECRET_ARN": api_service_account_secret_arn,
            "USERNAME_PERSON_LINK_TABLE_NAME": username_person_link_table.table.table_name,
            "USERNAME_PERSON_LINK_TABLE_PERSON_INDEX_NAME": username_person_link_table.person_gsi_index_name,
            "ACCESS_REQUEST_EMAIL_ADDRESS": access_alerts_email_address,
            "GIT_COMMIT_ID": git_commit_id,
            "MONITORING_ENABLED": str(sentry_config.monitoring_enabled),
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
            handler=cast(_lambda.IFunction, api_func.function),

            # Greedy proxy forwards all traffic at endpoint
            # to lambda
            proxy=True,
            domain_name=api_gw.DomainNameOptions(
                domain_name=f"{domain}.{allocator.root_domain}",
                certificate=acm_cert
            ),
            deploy_options=api_gw.StageOptions(
                description="Auth API Docker Lambda FastAPI API Gateway",
                throttling_burst_limit=api_rate_limiting.throttling_burst_limit if api_rate_limiting else None,
                throttling_rate_limit=api_rate_limiting.throttling_rate_limit if api_rate_limiting else None,
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="lambda-auth-api-route",
            target=api,
            domain=domain,
            comment="Lambda Auth API domain entry"
        )

        # Add rule to listener to hit this target group
        target_host = domain + "." + allocator.root_domain

        # enable the API to read the service account secret
        auth_service_secret = sm.Secret.from_secret_complete_arn(
            self, 'service-account', api_service_account_secret_arn
        )
        auth_service_secret.grant_read(api_func.function.role)

        # expose endpoint
        self.endpoint = f"https://{target_host}"

        # expose tables
        self.access_request_table = access_request_table.table
        self.groups_table = user_groups_table.table
        self.username_person_link_table = username_person_link_table.table
        self.add_api_environment = api_func.function.add_environment
