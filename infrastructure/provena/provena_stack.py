from aws_cdk import (
    Stack,
    CfnOutput,
    aws_backup as backup,
    aws_kms as kms,
    aws_ecs as ecs,
    aws_secretsmanager as aws_sm,
    Aspects,
    Duration,
    Tags
)
from constructs import Construct
from provena.aspects import removal_policy, ddb_on_demand
from provena.component_constructs.data_store_lambda_api import LambdaDataStoreAPI
from provena.component_constructs.search_lambda_api import LambdaSearchAPI
from provena.component_constructs.auth_lambda_api import LambdaAuthApi
from provena.component_constructs.keycloak_infrastructure import KeycloakConstruct
from provena.component_constructs.network_construct import NetworkConstruct
from provena.component_constructs.identity_service import IdentityService
from provena.component_constructs.registry_api import RegistryAPI
from provena.component_constructs.jobs.AsyncJobInfra import AsyncJobInfra, JobType, JobConfig
from provena.component_constructs.prov_api import ProvAPI
from provena.component_constructs.registry_table import RegistryTable, IdIndexTable
from provena.component_constructs.static_cloudfront_distribution import StaticCloudfrontDistribution
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.load_balancers import SharedBalancers
from provena.custom_constructs.lambda_warmer import LambdaWarmer, WarmerEndpoints
from provena.component_constructs.neo4j_ecs import Neo4jECS
from provena.component_constructs.backups import BackupService
from provena.component_constructs.search_infra import OpenSearchCluster
from provena.component_constructs.search_streamers import SearchStreamers, StreamerConfiguration, SearchableObject
from provena.utility.direct_secret_import import direct_import
from provena.utility.hash_dir import hash_dir_list
from provena.config.config_class import *
from provena.config.config_helpers import resolve_endpoints
from typing import Optional, Any, List


def get_priority(used_priorities: List[int]) -> int:
    priority = max(used_priorities) + 1
    used_priorities.append(priority)
    return priority


class ProvenaStack(Stack):
    def __init__(self,
                 scope: Construct,
                 id: str,
                 config: ProvenaConfig,
                 **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # resolve endpoints statically in case where we have circular
        # dependencies
        resolved_endpoints = resolve_endpoints(config=config)

        # if feature deployment, apply broad removal policy to help ensure
        # resources are cleaned up on deletion - this uses CDK Aspects to
        # traverse the node tree
        if config.deployment.feature_deployment:
            Aspects.of(self).add(removal_policy.RemovalPolicyAspect())

        # Ensure we don't accidentally provision any CfnTables which have
        # provisioned throughput
        Aspects.of(self).add(ddb_on_demand.DynamoDBOnDemandOnly())

        # add tags for all child components where tagging is possible
        tags: Dict[str, str] = config.general.tags

        # Add tags
        for k, v in tags.items():
            Tags.of(self).add(
                key=k,
                value=v
            )

        # work out keycloak endpoints
        if config.components.keycloak is not None:
            auth_domain = config.components.keycloak.domain
            root_domain = config.dns.root_domain
            realm_name = config.components.keycloak.realm_name
            keycloak_auth_endpoint_full = f"https://{auth_domain}.{root_domain}/auth/realms/{realm_name}"
            keycloak_auth_endpoint_minimal = f"https://{auth_domain}.{root_domain}/auth"
            # Keycloak issuer is used for OIDC service relationship on STS assume role with web identity call
            # e.g. auth.dev.provena.io
            keycloak_issuer = f"{auth_domain}.{root_domain}"
        else:
            # using some shared keycloak endpoint
            assert config.general.keycloak_endpoints
            keycloak_auth_endpoint_full = config.general.keycloak_endpoints.full_endpoint
            keycloak_auth_endpoint_minimal = config.general.keycloak_endpoints.minimal_endpoint
            # Keycloak issuer is used for OIDC service relationship on STS assume role with web identity call
            # e.g. auth.dev.provena.io
            keycloak_issuer = config.general.keycloak_endpoints.issuer

        balancers: Optional[SharedBalancers] = None
        used_priorities: List[int] = [0]

        # pull out some common vars
        stage = config.deployment.stage
        branch_name = config.deployment.git_branch_name
        build_token_arn = config.deployment.github_token_arn
        cert_arn = config.dns.domain_certificate_arn
        us_east_cert_arn = config.dns.us_east_certificate_arn
        root_domain = config.dns.root_domain

        network: Optional[NetworkConstruct] = None
        # networking is required
        if config.components.networking:
            # Create basic network
            network = NetworkConstruct(
                scope=self,
                construct_id="net",
                stage=stage
            )

            balancers = network.balancers

        # pull out service role arn from OIDC provider
        # either from the keycloak deployment (ideally)
        # or in the case of the test branch, we need to pull it out
        # specially - bit fragile
        oidc_service_role_arn: str

        # conditionally deploy keycloak
        if config.components.keycloak:
            # make sure network was setup
            assert network

            # ensure we have CMK from key manager
            db_key = kms.Key(
                scope=self,
                id='db-key',
                alias=stage + '-db-cmk',
                description='CMK used to encrypt database snapshots'
            )

            # deploy KC infra
            assert balancers, "Balancers object should be present"

            priority = get_priority(used_priorities)

            kc_config = config.components.keycloak

            # Create KeyCloak construct
            kc_construct = KeycloakConstruct(
                scope=self,
                construct_id="kc",
                stage=stage,
                realm_name=kc_config.realm_name,
                custom_theme_name=kc_config.custom_theme_name,
                vpc=network.vpc,
                bucket_arn=config.general.storage_bucket_arn,
                cert_arn=config.dns.domain_certificate_arn,
                kc_db_instance_snapshot_arn=kc_config.snapshot_arn,
                kc_domain=kc_config.domain,
                dockerhub_creds_arn=config.general.dockerhub_creds_arn,
                hosted_zone_name=config.dns.hosted_zone_name,
                hosted_zone_id=config.dns.hosted_zone_id,
                balancers=balancers,
                http_listener_priority=priority,
                https_listener_priority=priority,
                rds_removal_policy=kc_config.rds_removal_policy,
                initial_configuration=kc_config.keycloak_configuration
            )
            # This is redundant
            # keycloak_auth_endpoint = kc_construct.keycloak_auth_endpoint
            dns_allocator = kc_construct.dns_allocator
            oidc_service_role_arn = kc_construct.oidc_bucket_service_role.role_arn

        # If we don't deploy keycloak - we need to know the auth endpoint that is
        # shared - this comes from parameter
        else:
            # Create allocator to use
            dns_allocator = DNSAllocator(
                scope=self,
                construct_id="dns",
                hosted_zone_id=config.dns.hosted_zone_id,
                hosted_zone_name=config.dns.hosted_zone_name
            )

            if (stage not in ["TEST", "DEV"]):
                assert False, "Trying to assume role ARN on non TEST stage."

            #! This is a fragile operation and could be improved
            oidc_service_role_arn = f"arn:aws:iam::{Stack.of(self).account}:role/DEV-oidc_bucket_service"

        # expose the minimal endpoint value
        self.keycloak_auth_endpoint_minimal_cfn = CfnOutput(
            self, 'kcendpoint', value=keycloak_auth_endpoint_minimal)
        self.keycloak_auth_endpoint_cfn = CfnOutput(
            self, 'kcendpointfull', value=keycloak_auth_endpoint_full)

        # =======================
        # Handle/Identity Service
        # =======================

        # Create Identity service construct
        # this is unique for each stack
        id_service: Optional[IdentityService] = None
        if config.components.identity_service:
            id_config = config.components.identity_service
            id_service = IdentityService(
                scope=self,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                domain_base=config.general.application_root_domain,
                construct_id='id',
                stage=stage,
                handle_secret_arn=id_config.handle_credentials_arn,
                handle_endpoint=id_config.ardc_service_endpoint,
                build_github_token_arn=build_token_arn,
                keycloak_auth_endpoint=keycloak_auth_endpoint_full,
                cert_arn=cert_arn,
                domain=id_config.domain_name,
                allocator=dns_allocator,
                extra_hash_dirs=id_config.extra_hash_dirs,
                git_commit_id=config.deployment.git_commit_id,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
                api_rate_limiting=config.general.rate_limiting,
            )

        # ========
        # Auth API
        # ========
        auth_api: Optional[LambdaAuthApi] = None
        if config.components.auth_api:
            # Create auth api service
            # Lambda version currently in use
            auth_config = config.components.auth_api

            # depends on the registry api component
            assert config.components.entity_registry, "Cannot deploy auth API without registry"
            auth_api = LambdaAuthApi(
                self,
                domain_base=config.general.application_root_domain,
                construct_id='auth-api',
                stage=stage,
                extra_hash_dirs=auth_config.extra_hash_dirs,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                github_build_token_arn=build_token_arn,
                domain=auth_config.api_domain,
                keycloak_endpoint=keycloak_auth_endpoint_full,
                api_service_account_secret_arn=auth_config.api_service_account_secret_arn,
                allocator=dns_allocator,
                cert_arn=cert_arn,
                request_table_pitr=auth_config.pitr_request_table,
                api_rate_limiting=config.general.rate_limiting,
                access_alerts_email_address=auth_config.access_alerts_email_address,
                user_groups_table_pitr=auth_config.pitr_groups_table,
                request_table_removal_policy=auth_config.request_table_removal_policy,
                groups_table_removal_policy=auth_config.groups_table_removal_policy,
                # since we have a circular dependency here we need to resolve
                # the registry endpoint manually
                registry_api_endpoint=resolved_endpoints.registry_api,
                git_commit_id=config.deployment.git_commit_id,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
            )

            # Expose the endpoint
            self.auth_api_endpoint = CfnOutput(
                self, 'auth-api-endpoint-output',
                value=auth_api.endpoint
            )

        # ============
        # Landing Page
        # ============

        if config.components.landing_page:
            landing_config = config.components.landing_page
            # Create the landing page static UI website
            landing_page_ui = StaticCloudfrontDistribution(scope=self,
                                                           construct_id="landing-page-ui",
                                                           stage=stage,
                                                           us_east_cert_arn=us_east_cert_arn,
                                                           sub_domain=landing_config.ui_domain,
                                                           root_domain=root_domain,
                                                           trusted_build_accounts=config.deployment.trusted_ui_build_account_ids,
                                                           dns_allocator=dns_allocator)

            # Produce cfn output
            self.landing_page_ui_bucket_name = CfnOutput(
                scope=self,
                id="landing_page_ui_bucket_name",
                value=landing_page_ui.bucket_name)

        # =================================
        # SEARCH API and OpenSearch service
        # =================================

        # setup the search infra
        open_search_infra: Optional[OpenSearchCluster] = None
        search_api: Optional[LambdaSearchAPI] = None

        if config.components.search:
            search_config = config.components.search

            # cluster
            open_search_infra = OpenSearchCluster(
                scope=self,
                id='opensearch',
                cert_arn=cert_arn,
                hz=dns_allocator.hz,
                removal_policy=search_config.cluster_removal_policy,
                # this may not be defined depending on if we are reusing existing domain
                search_domain=search_config.search_service_domain,
                # conditionally include existing endpoint
                existing_domain_arn=search_config.existing_cluster_info.domain_arn if search_config.existing_cluster_info else None,
                existing_domain_endpoint=search_config.existing_cluster_info.domain_endpoint if search_config.existing_cluster_info else None,
            )

            search_domain = open_search_infra.domain

            # Search API
            search_api = LambdaSearchAPI(
                scope=self,
                construct_id='search-api',
                domain_base=config.general.application_root_domain,
                stage=stage,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                linearised_field_name=search_config.linearised_field_name,
                extra_hash_dirs=search_config.api_hash_dirs,
                domain=search_config.api_domain,
                github_build_token_arn=build_token_arn,
                keycloak_endpoint=keycloak_auth_endpoint_full,
                allocator=dns_allocator,
                cert_arn=cert_arn,
                api_rate_limiting=config.general.rate_limiting,
                unqualified_search_domain=open_search_infra.unqualified_domain_endpoint,
                registry_index=search_config.registry_index_name,
                global_index=search_config.global_index_name,
                git_commit_id=config.deployment.git_commit_id,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
            )

            # Expose the endpoint
            self.search_api_endpoint = CfnOutput(
                self, 'search-api-endpoint-output',
                value=search_api.endpoint
            )

            # grants read/write to the required indexes
            search_domain.grant_read_write(search_api.function)

        # ===================================
        # Entity Registry API and Tables + UI
        # ===================================

        registry_table: Optional[RegistryTable] = None
        lock_table: Optional[IdIndexTable] = None
        auth_table: Optional[IdIndexTable] = None
        registry_api: Optional[RegistryAPI] = None

        if config.components.entity_registry:
            reg_config = config.components.entity_registry

            # depends on auth api
            assert auth_api

            # depends on the id service
            assert id_service

            # Create table for registry
            registry_table = RegistryTable(
                scope=self,
                construct_id='entity-registry',
                pitr_enabled=reg_config.pitr_enabled,
                readers=[],
                writers=[],
                removal_policy=reg_config.tables_removal_policy
            )
            auth_table = IdIndexTable(
                scope=self,
                construct_id='entity-registry-auth',
                pitr_enabled=reg_config.pitr_enabled,
                readers=[],
                writers=[],
                removal_policy=reg_config.tables_removal_policy
            )
            lock_table = IdIndexTable(
                scope=self,
                construct_id='entity-registry-lock',
                pitr_enabled=reg_config.pitr_enabled,
                readers=[],
                writers=[],
                removal_policy=reg_config.tables_removal_policy
            )
            # Create lambda API for registry
            registry_api = RegistryAPI(
                scope=self,
                construct_id='entity-registry-api',
                domain_base=config.general.application_root_domain,
                stage=stage,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                extra_hash_dirs=reg_config.extra_hash_dirs,
                github_build_token_arn=build_token_arn,
                domain=reg_config.api_domain,
                keycloak_endpoint=keycloak_auth_endpoint_full,
                handle_endpoint=id_service.handle_endpoint,
                api_service_account_secret_arn=reg_config.service_account_arn,
                allocator=dns_allocator,
                registry_table=registry_table,
                auth_table=auth_table,
                lock_table=lock_table,
                cert_arn=cert_arn,
                auth_api_endpoint=auth_api.endpoint,
                api_rate_limiting=config.general.rate_limiting,
                git_commit_id=config.deployment.git_commit_id,
                git_commit_url=config.deployment.git_commit_url,
                git_tag_name=config.deployment.git_tag_name,
                git_release_title=config.deployment.git_release_title,
                git_release_url=config.deployment.git_release_url,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
            )

            self.registry_api_endpoint = CfnOutput(
                self, 'registry-api-endpoint-output',
                value=registry_api.endpoint
            )

            # Create the registry static UI website
            registry_ui = StaticCloudfrontDistribution(
                scope=self,
                construct_id="registry-ui",
                stage=stage,
                us_east_cert_arn=us_east_cert_arn,
                sub_domain=reg_config.ui_domain,
                root_domain=root_domain,
                trusted_build_accounts=config.deployment.trusted_ui_build_account_ids,
                dns_allocator=dns_allocator
            )

            # Produce cfn output
            self.registry_ui_bucket_name = CfnOutput(
                scope=self,
                id="registry_ui_bucket_name",
                value=registry_ui.bucket_name)

        # ============
        # DATA STORE
        # ============

        ds_ui: Optional[StaticCloudfrontDistribution] = None
        data_api: Optional[LambdaDataStoreAPI] = None

        if config.components.data_store:
            # need the id service and auth_api + registry
            assert id_service
            assert auth_api
            assert registry_api

            ds_config = config.components.data_store
            # Create the data store static UI website
            ds_ui = StaticCloudfrontDistribution(
                scope=self,
                construct_id="data-store-ui",
                stage=stage,
                us_east_cert_arn=us_east_cert_arn,
                sub_domain=ds_config.ui_domain,
                root_domain=root_domain,
                dns_allocator=dns_allocator,
                trusted_build_accounts=config.deployment.trusted_ui_build_account_ids
            )

            # Produce cfn output
            self.data_store_ui_bucket_name = CfnOutput(
                scope=self,
                id="data_store_ui_bucket_name",
                value=ds_ui.bucket_name)

            # System's Dataset Reviewers Table
            reviewers_table = IdIndexTable(
                scope=self,
                construct_id='data-store-reviewers',
                pitr_enabled=reg_config.pitr_enabled,
                readers=[],
                writers=[],
                # same removal policy as registry tables
                removal_policy=reg_config.tables_removal_policy
            )

            data_api = LambdaDataStoreAPI(
                self,
                construct_id='data-api',
                domain_base=config.general.application_root_domain,
                stage=stage,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                domain=ds_config.api_domain,
                extra_hash_dirs=ds_config.extra_hash_dirs,
                github_build_token_arn=build_token_arn,
                keycloak_endpoint=keycloak_auth_endpoint_full,
                keycloak_issuer=keycloak_issuer,
                handle_endpoint=id_service.handle_endpoint,
                auth_api_endpoint=auth_api.endpoint,
                registry_api_endpoint=registry_api.endpoint,
                api_service_account_secret_arn=ds_config.service_account_arn,
                oidc_service_account_secret_arn=ds_config.oidc_service_account_arn,
                api_rate_limiting=config.general.rate_limiting,
                oidc_service_role_arn=oidc_service_role_arn,
                storage_bucket_arn=config.general.storage_bucket_arn,
                allocator=dns_allocator,
                reviewers_table=reviewers_table,
                # Include registry for permissions and
                # env variable injection
                cert_arn=cert_arn,
                git_commit_id=config.deployment.git_commit_id,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
            )

            # Expose the endpoint
            self.data_api_endpoint = CfnOutput(
                self, 'data-api-endpoint-output',
                value=data_api.endpoint
            )

        # ==========================
        # Prov API, UI and Neo4j ECS
        # ==========================

        if config.components.prov_store:
            # requires registry api, data api, network and balancers
            assert network
            assert balancers
            assert data_api
            assert registry_api

            prov_config = config.components.prov_store

            priority = get_priority(used_priorities)

            # ECS which hosts neo4j graph DB from EFS
            neo4j_ecs = Neo4jECS(
                scope=self,
                id='neo4j',
                stage=stage,
                http_instance_domain=prov_config.neo4j_http_domain,
                bolt_instance_domain=prov_config.neo4j_bolt_domain,
                neo4j_auth_arn=prov_config.neo4j_auth_arn,
                neo4j_memory_size=prov_config.neo4j_memory_size,
                neo4j_cpu_size=prov_config.neo4j_cpu_size,
                vpc=network.vpc,
                balancers=balancers,
                http_priority=priority,
                allocator=dns_allocator,
                efs_root_path=prov_config.neo4j_efs_root_path,
                service_instance_role_arn=prov_config.neo4j_service_instance_role_arn,
                efs_removal_policy=prov_config.neo4j_efs_removal_policy
            )

            # Create lambda prov api
            prov_api: ProvAPI = ProvAPI(
                scope=self,
                construct_id='prov-api',
                stage=stage,
                domain_base=config.general.application_root_domain,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                github_build_token_arn=build_token_arn,
                extra_hash_dirs=prov_config.extra_hash_dirs,
                domain=prov_config.api_domain,
                keycloak_endpoint=keycloak_auth_endpoint_full,
                service_account_secret_arn=prov_config.service_account_arn,
                allocator=dns_allocator,
                cert_arn=cert_arn,
                neo4j_host=neo4j_ecs.neo4j_bolt_host,
                api_rate_limiting=config.general.rate_limiting,
                neo4j_port=str(neo4j_ecs.neo4j_bolt_port),
                neo4j_auth_arn=prov_config.neo4j_auth_arn,
                registry_api_endpoint=registry_api.endpoint,
                data_store_api_endpoint=data_api.endpoint,
                git_commit_id=config.deployment.git_commit_id,
                sentry_config=config.deployment.sentry_config,
                feature_number=config.deployment.ticket_no,
            )

            self.prov_api_endpoint = CfnOutput(
                self, 'prov-api-endpoint-output',
                value=prov_api.endpoint
            )

            # Create the prov static UI website
            prov_ui = StaticCloudfrontDistribution(scope=self,
                                                   construct_id="prov-ui",
                                                   stage=stage,
                                                   us_east_cert_arn=us_east_cert_arn,
                                                   sub_domain=prov_config.ui_domain,
                                                   root_domain=root_domain,
                                                   dns_allocator=dns_allocator)

            # Produce cfn output
            self.prov_ui_bucket_name = CfnOutput(
                scope=self,
                id="prov_ui_bucket_name",
                value=prov_ui.bucket_name)

        # Lambda DynamoDB streamers for datasets/registry entities if desired
        if config.components.search:
            # we know the open search infra is setup
            assert open_search_infra

            search_config = config.components.search

            # Setup a set of lambda functions which stream dynamoDB events to the
            # open search cluster
            configs: List[StreamerConfiguration] = []
            if search_config.stream_registry:
                # requires the entity registry
                assert registry_table

                # entity registry
                configs.append(
                    StreamerConfiguration(
                        id='entity-registry',
                        index_name=search_config.registry_index_name,
                        dynamodb_table=registry_table.table,
                        primary_id_field_name="id",
                        item_type=SearchableObject.REGISTRY_ITEM
                    )
                )

            # this will setup record streamers from data registry and entity
            # registry tables
            streamers = SearchStreamers(
                scope=self,
                id='search-streamers',
                configs=configs,
                linearised_field_name=search_config.linearised_field_name,
                qualified_search_domain_name=open_search_infra.qualified_domain_endpoint,
                open_search_domain=open_search_infra.domain,
                github_token_arn=build_token_arn,
                branch_name=branch_name,
                repo_string=config.deployment.git_repo_string,
                extra_hash_dirs=search_config.streamer_extra_hash_dirs
            )


        # Job Infrastructure
        assert prov_api
        github_token = direct_import(
            config.deployment.github_token_arn, Stack.of(self).region)

        # TODO Clean this up
        prov_lodge_environment = prov_api.prov_api_environment.copy()
        assert registry_api
        # This can be optional - so filter for non None only
        registry_job_environment: Dict[str, str] = {
            k: v for k, v in registry_api.registry_api_environment.items() if v is not None}

        # Email connection secret

        email_secret = aws_sm.Secret.from_secret_complete_arn(
            scope=self, id='email-secret', secret_complete_arn=config.general.email_connection_secret_arn
        )

        assert network
        async_config = config.components.async_jobs
        assert async_config
        jobs: List[JobConfig] = [
            JobConfig(type=JobType.PROV_LODGE,
                      image=ecs.ContainerImage.from_asset(
                          directory="../prov-api",
                          file="JobDockerfile",
                          build_args={
                              "github_token": github_token,
                              "repo_string": config.deployment.git_repo_string,
                              "branch_name": config.deployment.git_branch_name,
                              "CACHE_BUSTER": hash_dir_list(async_config.prov_job_extra_hash_dirs)
                          },
                      ),
                      visibility_timeout=Duration.minutes(5),
                      # All tasks get the queue url, status table name, job type and sns
                      # topic by default - these are added in
                      environment=prov_lodge_environment,
                      secrets={}
                      ),
            JobConfig(type=JobType.REGISTRY,
                      image=ecs.ContainerImage.from_asset(
                          directory="../registry-api",
                          file="JobDockerfile",
                          build_args={
                              "github_token": github_token,
                              "repo_string": config.deployment.git_repo_string,
                              "branch_name": config.deployment.git_branch_name,
                              "CACHE_BUSTER": hash_dir_list(async_config.registry_job_extra_hash_dirs)
                          },
                      ),
                      visibility_timeout=Duration.minutes(5),
                      # All tasks get the queue url, status table name, job type and sns
                      # topic by default - these are added in
                      environment=registry_job_environment,
                      secrets={}
                      ),
            JobConfig(type=JobType.EMAIL,
                      image=ecs.ContainerImage.from_asset(
                          directory="../services/email-service",
                          file="Dockerfile",
                          build_args={
                              "github_token": github_token,
                              "repo_string": config.deployment.git_repo_string,
                              "branch_name": config.deployment.git_branch_name,
                              "CACHE_BUSTER": hash_dir_list(async_config.email_job_extra_hash_dirs)
                          },
                      ),
                      visibility_timeout=Duration.minutes(5),
                      # All tasks get the queue url, status table name, job type and sns
                      # topic by default - these are added in
                      environment={},
                      secrets={
                          # Connection information
                          'port': ecs.Secret.from_secrets_manager(
                              secret=email_secret,
                              field="port"
                          ),
                          # smtp_server: str
                          'smtp_server': ecs.Secret.from_secrets_manager(
                              secret=email_secret,
                              field="smtp_server"
                          ),
                          # Username/password
                          # username: str
                          'username': ecs.Secret.from_secrets_manager(
                              secret=email_secret,
                              field="username"
                          ),
                          # password: SecretStr
                          'password': ecs.Secret.from_secrets_manager(
                              secret=email_secret,
                              field="password"
                          ),
                          # Email from address
                          # email_from: str
                          'email_from': ecs.Secret.from_secrets_manager(
                              secret=email_secret,
                              field="email_from"
                          )
                      }
                      )
        ]

        async_infra: AsyncJobInfra = AsyncJobInfra(
            scope=self,
            construct_id='async',
            stage=stage,
            jobs=jobs,
            idle_timeout=async_config.async_idle_timeout,
            max_task_scaling=async_config.max_task_scaling,
            cert_arn=config.dns.domain_certificate_arn,
            allocator=dns_allocator,
            keycloak_endpoint=keycloak_auth_endpoint_full,
            domain=async_config.job_api_domain,
            domain_base=config.general.application_root_domain,
            github_build_token_arn=config.deployment.github_token_arn,
            repo_string=config.deployment.git_repo_string,
            branch_name=config.deployment.git_branch_name,
            api_rate_limiting=config.general.rate_limiting,
            vpc=network.vpc,
            job_api_extra_hash_dirs=async_config.job_api_extra_hash_dirs,
            invoker_extra_hash_dirs=async_config.invoker_extra_hash_dirs,
            connector_extra_hash_dirs=async_config.connector_extra_hash_dirs,
            git_commit_id=config.deployment.git_commit_id,
            sentry_config=config.deployment.sentry_config,
            feature_number=config.deployment.ticket_no,
        )
        
        # Lambda integrated warmer API
        if config.components.warmer is not None:
            warmer_config = config.components.warmer
            warmer = LambdaWarmer(
                scope=self,
                id='warmer',
                sub_domain=warmer_config.domain,
                cert_arn=config.dns.domain_certificate_arn,
                allocator=dns_allocator,
                endpoints=WarmerEndpoints(
                    DATA_STORE_API_ENDPOINT=data_api.endpoint if data_api else None,
                    REGISTRY_API_ENDPOINT=registry_api.endpoint if registry_api else None,
                    PROV_API_ENDPOINT=prov_api.endpoint if prov_api else None,
                    HANDLE_API_ENDPOINT=id_service.handle_endpoint if id_service else None,
                    AUTH_API_ENDPOINT=auth_api.endpoint if auth_api else None,
                    SEARCH_API_ENDPOINT=search_api.endpoint if search_api else None,
                    JOB_API_ENDPOINT=async_infra.job_api_endpoint if async_infra else None
                ),
                api_rate_limiting=config.general.rate_limiting,
            )
            # Expose the endpoint
            self.warmer_api_endpoint = CfnOutput(
                self, 'warmer-api-endpoint-output',
                value=warmer.endpoint
            )

        # Expose the endpoint
        self.job_api_endpoint = CfnOutput(
            self, 'job-api-endpoint-output',
            value=async_infra.job_api_endpoint
        )

        # Update data store API with job api endpoint
        assert data_api
        data_api.add_api_environment(
            "job_api_endpoint", async_infra.job_api_endpoint)

        # Update auth API with job api endpoint
        assert auth_api
        auth_api.add_api_environment(
            "job_api_endpoint", async_infra.job_api_endpoint)

        # Update the registry API with the job API endpoint
        registry_api.add_to_environment(
            "job_api_endpoint", async_infra.job_api_endpoint)
        # This sets up the prov job ECS task dfn to have equivalent
        # permissions/rights as the prov API
        registry_api.grant_api_equivalent_permissions(
            async_infra.task_roles[JobType.REGISTRY])

        # Update the prov API with the job API endpoint
        prov_api.add_to_environment(
            "job_api_endpoint", async_infra.job_api_endpoint)
        # This sets up the prov job ECS task dfn to have equivalent
        # permissions/rights as the prov API
        prov_api.grant_equivalent_permissions(
            async_infra.task_roles[JobType.PROV_LODGE])

        # Add permissions to job

        # Configure AWS backup if required
        backup_config = config.backup
        extra_name_prefix = config.general.extra_name_prefix

        if backup_config.backups_enabled:
            self.backup_service = BackupService(
                scope=self,
                id='backup',
                existing_vault_arn=backup_config.existing_vault_arn,
                alias_name=f"{stage}_{backup_config.vault_name}_kms_key",
                vault_name=backup_config.vault_name,
                critical_plan_name=f"{extra_name_prefix + '-' if extra_name_prefix else ''}{stage}-critical-backup-plan",
                non_critical_plan_name=f"{extra_name_prefix + '-' if extra_name_prefix else ''}{stage}-non-critical-backup-plan",
                data_storage_plan_name=f"{extra_name_prefix + '-' if extra_name_prefix else ''}{stage}-data-storage-backup-plan",
                trusted_copy_source_account_ids=backup_config.trusted_copy_source_account_ids,
                trusted_copy_destination_account_ids=backup_config.trusted_copy_destination_account_ids,
                key_admins=backup_config.key_admins
            )

            def backup_helper(id: str, type: BackupType, resource: backup.BackupResource) -> None:
                if type == BackupType.NONE:
                    return
                if type == BackupType.CRITICAL:
                    self.backup_service.register_critical_resource(
                        id=id,
                        resource=resource
                    )
                    return
                if type == BackupType.NON_CRITICAL:
                    self.backup_service.register_non_critical_resource(
                        id=id,
                        resource=resource
                    )
                    return
                if type == BackupType.DATA_STORAGE:
                    self.backup_service.register_data_storage_resource(
                        id=id,
                        resource=resource,
                        # special flag to add s3 permissions
                        enable_s3_permissions=True
                    )
                    return
                raise ValueError("Couldn't parse type of BackupType enum")

            # Add targets to configured plans

            # Registry
            if config.components.entity_registry:
                assert registry_table
                assert lock_table
                assert auth_table

                reg_config = config.components.entity_registry

                # registry tables
                backup_helper(
                    id="entity-registry-resource-table",
                    type=reg_config.tables_backup_policy,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=registry_table.table)
                )
                backup_helper(
                    id="entity-registry-lock-table",
                    type=reg_config.tables_backup_policy,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=lock_table.table)
                )
                backup_helper(
                    id="entity-registry-auth-table",
                    type=reg_config.tables_backup_policy,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=auth_table.table)
                )

            if config.components.auth_api:
                assert auth_api
                auth_config = config.components.auth_api
                # Auth request table
                backup_helper(
                    id="access-request-table",
                    type=auth_config.backup_request_table,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=auth_api.access_request_table)
                )
                # Groups table
                backup_helper(
                    id="auth-groups-table",
                    type=auth_config.backup_groups_table,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=auth_api.groups_table
                    )
                )
                # Username <-> Person link table
                backup_helper(
                    id="username-person-link-table",
                    type=auth_config.backup_username_person_link_table,
                    resource=backup.BackupResource.from_dynamo_db_table(
                        table=auth_api.username_person_link_table
                    )
                )

            # S3 bucket
            backup_helper(
                id="data-store-bucket",
                type=config.general.storage_bucket_backup_policy,
                resource=backup.BackupResource.from_arn(
                    config.general.storage_bucket_arn)
            )

            # neo4j EFS
            if config.components.prov_store:
                assert neo4j_ecs
                backup_helper(
                    id="neo4j-file-system",
                    type=config.components.prov_store.efs_backup_policy,
                    resource=backup.BackupResource.from_efs_file_system(
                        neo4j_ecs.file_system)
                )

            # keycloak database
            if config.components.keycloak:
                # make sure the construct exists
                assert kc_construct

                backup_helper(
                    id="keycloak-rds",
                    type=config.components.keycloak.rds_backup_policy,
                    resource=backup.BackupResource.from_rds_database_instance(
                        kc_construct.db_instance_construct.instance)
                )
