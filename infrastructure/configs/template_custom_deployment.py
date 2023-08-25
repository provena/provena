#!/usr/bin/env python3
from aws_cdk import (
    aws_codepipeline_actions as cp_actions,
    Environment
)
from configs.version_helpers import *
from provena.config.config_class import *
from provena.config.config_global_defaults import *

from typing import List, Tuple

"""
This python file defines an example PROD stage Provena deployment. The values
are replaced with TODO where you should update them. This accompanies the
Confluence guide on how to deploy Provena from Scratch.

Start by making a copy of this file to edit.

When you have filled out the values according to the guide.

Then update the config_map to import this config.

Assuming this config id is "CONFIG" you can run it using the following function:

To run CDK actions against the Pipeline stack

python app_run.py CONFIG pipeline <synth/deploy/destroy>

To run CDK actions against the Application stack

python app_run.py CONFIG app <synth/deploy/destroy>
"""


# ==================
# VALIDATION HELPERS
# ==================

# list of name, val
todo_checker_list: List[Tuple[str, str]] = []


def register_checker(name: str, var: str) -> None:
    todo_checker_list.append((name, var))


def check_vars() -> None:
    for name, val in todo_checker_list:
        if val == "TODO":
            raise ValueError(
                f"Variable {name = } is incomplete (TODO). Deployment aborted.")

# ================
# HELPER FUNCTIONS
# ================


def postfix_domain(domain: str) -> str:
    # no postfixing required
    return domain

# ==================
# AWS ACCOUNT TARGET
# ==================


aws_account_id = "TODO"
register_checker(name="aws_account_id", var=aws_account_id)

aws_region = "TODO"
register_checker(name="aws_region", var=aws_region)

account_env = Environment(
    account=aws_account_id,
    region=aws_region
)

# ================
# APPLICATION TAGS
# ================

# TODO What tags do you want on your AWS resources. e.g. author, application,
# date, description, etc...
tags: Dict[str, str] = {}

# =========
# APP STAGE
# =========

# this defines the name of the config ID - you will need to update config_map to
# map against this config ID after importing it
config_id = "TODO"
register_checker(name="config_id", var=config_id)

# TODO validate desired deployment stage
app_stage: Stage = Stage.PROD

# ===========
# STACK NAMES
# ===========

# What name should the pipeline Cfn stack have e.g. PRODPipeline
pipeline_stack_id: str = "TODO"
register_checker(name="pipeline_stack_id", var=pipeline_stack_id)

# What name should the application stack have
deployment_stack_id: str = "TODO"
register_checker(name="deployment_stack_id", var=deployment_stack_id)

# ========
# UI THEME
# ========

default_ui_theme = UI_DEFAULT_THEME_ID

# What UI theme would you like to use? If you want to use the default Provena
# theme, just specify the default above. Otherwise, you can use your own theme
# ID by providing the matching theme id

# TODO select your UI theme
ui_theme_id = "TODO"
register_checker("ui_theme_id", ui_theme_id)

# ===================
# EMAIL CONFIGURATION
# ===================

# TODO Are pipeline alerts activated? And if so, what email address?
pipeline_alerts_activated: bool = False
pipeline_alerts_email_address: Optional[str] = None

# TODO What email address to send access alerts to?
access_alerts_email_address="TODO"
register_checker("access_alerts_email_address", access_alerts_email_address)

# ==================
# OPTIONAL PIPELINES
# ==================

# TODO Include additional quick deploy pipeline that by passes tests for faster development?
quick_deploy_pipeline_activated: bool = False

# ==================================
# DOCUMENTATION AND CONTACT US LINKS
# ==================================

# What is the base path of the documentation URL - this is postfixed with
# specific help links based on the Provena github pages deployment. To use the
# Provena docs, change the variable to default_docs below.

default_docs = DEFAULT_DOCUMENTATION_BASE_URL  # provena docs
documentation_base_url = "TODO"
register_checker(name="documentation_base_url", var=documentation_base_url)

# What link should open in a new tab when the contact us button is pressed?
contact_us_link = "TODO"
register_checker(name="contact_us_link", var=contact_us_link)

# ==============
# HANDLE SERVICE
# ==============

# What is the ARDC handle credentials secret ARN?
handle_secret_arn = "TODO"
register_checker(name="handle_secret_arn", var=handle_secret_arn)

# What is the ARDC endpoint being used?
# if prod creds then use PROD_ARDC_SERVICE_ENDPOINT
# if test creds then use TEST_ARDC_SERVICE_ENDPOINT
ardc_endpoint: str = PROD_ARDC_SERVICE_ENDPOINT

# =======================================
# REFERENCES TO SECRETS AND CONFIGURATION
# =======================================

# Pre-existing S3 bucket used for storage, ensure Versioning is enabled and
# public access disabled
bucket_arn = "TODO"
register_checker(name="bucket_arn", var=bucket_arn)

# Neo4j service instance IAM role arn
neo4j_service_role_arn = "TODO"
register_checker(name="neo4j_service_role_arn", var=neo4j_service_role_arn)

# Neo4j authorisation credentials - see guide for format
neo4j_auth_arn = "TODO"
register_checker(name="neo4j_auth_arn", var=neo4j_auth_arn)

# Dockerhub account credentials - can be free tier account
dockerhub_credentials_arn = "TODO"
register_checker(name="dockerhub_credentials_arn",
                 var=dockerhub_credentials_arn)

# Gmail authorisation configuration ARN
gmail_auth_arn = "TODO"
register_checker(name="gmail_auth_arn", var=gmail_auth_arn)

# ======================
# KEYCLOAK CONFIGURATION
# ======================

# (Optional) Keycloak PostgreSQL RDS instance snapshot

# -> If provided means keycloak bootstraps off existing RDS snapshot
# -> If not provided means keycloak deployment is on brand new RDS with
# preconfigured realm default
keycloak_snapshot_arn: Optional[str] = None

# What realm name do you want in your Keycloak instance? If redeploying, ensure
# you match the snapshotted instance realm
realm_name = "TODO"
register_checker(name="realm_name", var=realm_name)

# What is the theme name? This can be the default (KEYCLOAK_DEFAULT_THEME_NAME)
# or your custom created theme TODO
custom_theme_name = "TODO"
register_checker(name="custom_theme_name", var=custom_theme_name)

# in the deployed keycloak - what should the realm display name be - note that this is ignored if snapshot ARN provided
realm_display_name = "TODO"
register_checker(name="realm_display_name", var=realm_display_name)


# ============
# CERTIFICATES
# ============

# this is for ap-southeast-2 *.base and base
ap_certs_arn = "TODO"
register_checker(name="ap_certs_arn", var=ap_certs_arn)

# this is for us-east-1 *.base and base
us_certs_arn = "TODO"
register_checker(name="us_certs_arn", var=us_certs_arn)

# =======
# DOMAINS
# =======

# Root domain of the hosted zone - may not be the same as the application root
# domain e.g. provena.io
hz_root_domain = "TODO"
register_checker(name="hz_root_domain", var=hz_root_domain)

# This is the actual base domain that the app is deployed on - e.g.
# demo.provena.io the various components will be subdomains from this. The
# landing page will be apex record on this domain

# NOTE if your application root domain includes a prefix on your hz root domain,
# ensure you update the postfix domain method above. See dev_app.py for an
# example domain method above. See dev_app.py for an example.
application_root_domain = "TODO"
register_checker(name="application_root_domain", var=application_root_domain)

# This is the name of the hosted zone, usually the same as the hosted zone root
# domain
hosted_zone_name = "TODO"
register_checker(name="hosted_zone_name", var=hosted_zone_name)

# this it he hosted zone ID
hosted_zone_id = "TODO"
register_checker(name="hosted_zone_id", var=hosted_zone_id)

# ================
# SERVICE ACCOUNTS
# ================

# these provide credentials which APIs use to get service account permissions
# NOTE you can use scripts/bootstrap_secrets.sh to generate placeholder secrets
# pre keycloak deployment
data_store_api_service_account_arn = "TODO"
data_store_oidc_service_account_arn = "TODO"
registry_api_service_account_arn = "TODO"
prov_api_service_account_arn = "TODO"
prov_dispatcher_service_account_arn = "TODO"
auth_api_service_account_arn = "TODO"

register_checker(name="data_store_api_service_account_arn",
                 var=data_store_api_service_account_arn)
register_checker(name="data_store_oidc_service_account_arn",
                 var=data_store_oidc_service_account_arn)
register_checker(name="registry_api_service_account_arn",
                 var=registry_api_service_account_arn)
register_checker(name="prov_api_service_account_arn",
                 var=prov_api_service_account_arn)
register_checker(name="prov_dispatcher_service_account_arn",
                 var=prov_dispatcher_service_account_arn)
register_checker(name="auth_api_service_account_arn",
                 var=auth_api_service_account_arn)

# =================
# GIT CONFIGURATION
# =================

# What is the github OAuth token which can access your repo target?
github_token_arn = "TODO"
register_checker(name="github_token_arn", var=github_token_arn)

# what is the repo string - e.g. organisation/repo-name e.g. provena/provena
# Who is the github owner of the repo e.g. ScienceOrg101
git_owner_org = "TODO"
register_checker(name="git_owner_org", var=git_owner_org)
# What is the name of the repo e.g. provena
git_repo_name = "TODO"
register_checker(name="git_repo_name", var=git_repo_name)
# What branch is this deploying from?
branch_name = "TODO"
register_checker(name="branch_name", var=branch_name)

# ====================
# BACKUP CONFIGURATION
# ====================

# By default - the primary storage bucket is not backed up due to price
# considerations - you can enable this if you like
# TODO confirm this is correct for your deployment
s3_storage_backup_policy: BackupType = BackupType.NONE

# What should the name of the backup vault be - this should be unique between
# system deployments e.g. ProvenaBackupVault
backup_vault_name = "TODO"
register_checker(name="backup_vault_name", var=backup_vault_name)

# ===============================================================
# DEPLOYMENT (NO NEED TO MODIFY BELOW UNLESS IT REQUIRES CHANGES)
# ===============================================================


# Validate that all values provided (no TODO variables)
check_vars()

# setup keycloak conditional config
keycloak_config: Optional[KeycloakConfiguration] = None

# conditionally configure the keycloak configuration
if keycloak_snapshot_arn is None:
    keycloak_config = KeycloakConfiguration(
        display_name=realm_display_name,
        base_url=application_root_domain,
    )

static_config = ProvenaConfig(
    deployment=DeploymentConfig(
        config_id=config_id,
        pipeline_stack_id=pipeline_stack_id,
        deployment_stack_id=deployment_stack_id,
        stage=app_stage,
        git_owner_org=git_owner_org,
        git_repo_name=git_repo_name,
        git_branch_name=branch_name,
        git_commit_id=get_commit_id_from_env(),
        git_commit_url=get_commit_url_from_env(),
        git_tag_name=get_tag_name_from_env(),
        git_release_title=get_release_title_from_env(),
        git_release_url=get_release_url_from_env(),
        main_pipeline_trigger=aws_codepipeline_actions.GitHubTrigger.NONE,
        deployment_environment=account_env,
        pipeline_environment=account_env,
        github_token_arn=github_token_arn,
        cdk_app_name="provena_app.py",
        cdk_out_path=f"{app_stage.value.lower()}_cdk.out",
        quick_deploy_pipeline=quick_deploy_pipeline_activated,
        interface_pipeline=True,
        interface_pipeline_trigger_settings=cp_actions.GitHubTrigger.NONE,
        build_badge=BuildBadgeConfig(
            build_domain=postfix_domain(BUILD_BADGE_BUILD_PREFIX),
            interface_domain=postfix_domain(BUILD_BADGE_INTERFACE_PREFIX),
        ),
        ui_only_pipeline=True,
        ui_pipeline_trigger_settings=cp_actions.GitHubTrigger.NONE,
        email_alerts_activated=pipeline_alerts_activated,
        pipeline_alert_email=pipeline_alerts_email_address,
        cross_account=False,
        ci_hook_pr_into_branch=True,
        trusted_ui_build_account_ids=None,
        feature_deployment=False,
    ),
    components=ComponentConfig(
        async_jobs=AsyncJobsComponent(
            job_api_domain=postfix_domain(ASYNC_JOBS_API_DEFAULT_DOMAIN),
            job_api_extra_hash_dirs=ASYNC_JOB_API_EXTRA_HASH_DIRS,
            invoker_extra_hash_dirs=ASYNC_INVOKER_EXTRA_HASH_DIRS,
            connector_extra_hash_dirs=ASYNC_CONNECTOR_EXTRA_HASH_DIRS,
        ),
        warmer=LambdaWarmerComponent(
            domain=postfix_domain(WARMER_DEFAULT_DOMAIN)
        ),
        networking=NetworkingComponent(),
        keycloak=KeycloakComponent(
            domain=postfix_domain(AUTH_DEFAULT_DOMAIN),
            rds_backup_policy=BackupType.CRITICAL,
            snapshot_arn=keycloak_snapshot_arn,
            realm_name=realm_name,
            keycloak_configuration=keycloak_config,
            custom_theme_name=custom_theme_name
        ),
        identity_service=IdentityServiceComponent(
            handle_credentials_arn=handle_secret_arn,
            domain_name=postfix_domain(HANDLE_DEFAULT_DOMAIN),
            ardc_service_endpoint=ardc_endpoint,
            extra_hash_dirs=DEFAULT_EXTRA_HASH_DIRS,
        ),
        data_store=DataStoreComponent(
            service_account_arn=data_store_api_service_account_arn,
            oidc_service_account_arn=data_store_oidc_service_account_arn,
            api_domain=postfix_domain(DATA_DEFAULT_API_DOMAIN),
            ui_domain=postfix_domain(DATA_DEFAULT_UI_DOMAIN),
            pitr_enabled=True,
            table_backup_policy=BackupType.CRITICAL,
            extra_hash_dirs=DEFAULT_EXTRA_HASH_DIRS
        ),
        landing_page=LandingPageComponent(
            ui_domain=postfix_domain("")
        ),
        auth_api=AuthApiComponent(
            access_alerts_email_address=access_alerts_email_address,
            api_service_account_secret_arn=auth_api_service_account_arn,
            extra_hash_dirs=DEFAULT_EXTRA_HASH_DIRS,
            pitr_request_table=True,
            pitr_groups_table=True,
            backup_request_table=BackupType.NON_CRITICAL,
            backup_groups_table=BackupType.CRITICAL,
            backup_username_person_link_table=BackupType.CRITICAL,
            api_domain=postfix_domain(AUTH_API_DEFAULT_DOMAIN)
        ),
        search=SearchComponent(
            api_hash_dirs=DEFAULT_EXTRA_HASH_DIRS,
            streamer_extra_hash_dirs=DEFAULT_EXTRA_HASH_DIRS,
            existing_cluster_info=None,
            search_service_domain=postfix_domain(
                SEARCH_SERVICE_DEFAULT_DOMAIN),
            api_domain=postfix_domain(SEARCH_API_DEFAULT_DOMAIN),
            registry_index_name=DEFAULT_ENTITY_INDEX_NAME,
            global_index_name=DEFAULT_GLOBAL_INDEX_NAME,
            stream_registry=True
        ),
        entity_registry=EntityRegistryComponent(
            service_account_arn=registry_api_service_account_arn,
            extra_hash_dirs=REGISTRY_DEPENDANT_HASH_DIRS,
            api_domain=postfix_domain(REGISTRY_API_DEFAULT_DOMAIN),
            ui_domain=postfix_domain(REGISTRY_UI_DEFAULT_DOMAIN),
            pitr_enabled=True,
            tables_backup_policy=BackupType.CRITICAL,
        ),
        prov_store=ProvStoreComponent(
            extra_hash_dirs=JOB_ENABLED_API_EXTRA_HASH_DIRS,
            prov_job_extra_hash_dirs=DEFAULT_EXTRA_HASH_DIRS,
            api_domain=postfix_domain(PROV_API_DEFAULT_DOMAIN),
            ui_domain=postfix_domain(PROV_UI_DEFAULT_DOMAIN),
            neo4j_http_domain=postfix_domain(PROV_NEO4J_HTTP_DEFAULT_DOMAIN),
            neo4j_bolt_domain=postfix_domain(PROV_NEO4J_BOLT_DEFAULT_DOMAIN),
            neo4j_auth_arn=neo4j_auth_arn,
            neo4j_memory_size=SMALL_NEO4J_MEM_SIZE,
            neo4j_cpu_size=SMALL_NEO4J_CPU_SIZE,
            service_account_arn=prov_api_service_account_arn,
            neo4j_service_instance_role_arn=neo4j_service_role_arn,
            prov_job_dispatcher_service_role_secret_arn=prov_dispatcher_service_account_arn,
            neo4j_efs_root_path="/",
            efs_backup_policy=BackupType.CRITICAL,
        ),
    ),
    tests=TestConfig(
        test_activation={
            TestType.TS_TYPE_CHECK: True,
            TestType.MYPY_TYPE_CHECK: True,
            TestType.UNIT: True,
            TestType.INTEGRATION: False,
            # currently login tests won't work for stage/prod
            TestType.SYSTEM: False
        },
        unit_tests=UnitTestConfig(
            handle_secret_arn=handle_secret_arn,
            ardc_service_endpoint=TEST_ARDC_SERVICE_ENDPOINT
        ),
        # no integration tests
        integration_tests=None,
        # no config for system tests
        system_tests=None
    ),
    general=GeneralConfig(
        tags=tags,
        ui_theme_id=ui_theme_id,
        application_root_domain=application_root_domain,
        email_connection_secret_arn=gmail_auth_arn,
        dockerhub_creds_arn=dockerhub_credentials_arn,
        storage_bucket_arn=bucket_arn,
        storage_bucket_backup_policy=s3_storage_backup_policy,
        # we deploy keycloak - no need for this
        keycloak_endpoints=None,
        extra_name_prefix=None,
        documentation_base_link=documentation_base_url,
        contact_us_link=contact_us_link
    ),
    dns=DNSConfig(
        root_domain=hz_root_domain,
        hosted_zone_name=hosted_zone_name,
        hosted_zone_id=hosted_zone_id,
        domain_certificate_arn=ap_certs_arn,
        us_east_certificate_arn=us_certs_arn,
    ),
    backup=BackupConfig(
        backups_enabled=True,
        existing_vault_arn=None,
        vault_name=backup_vault_name,
        key_admins=[],
        trusted_copy_destination_account_ids=[],
        trusted_copy_source_account_ids=[]
    )
)


def config() -> ProvenaConfig:
    return static_config
