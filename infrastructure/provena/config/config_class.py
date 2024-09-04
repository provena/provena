from typing import Dict, Optional
from aws_cdk import Environment, aws_codepipeline_actions, RemovalPolicy
from typing import List
from enum import Enum
from pydantic import BaseModel
from provena.config.config_global_defaults import *

"""
    This class holds config information about deployment.

    In general, configuration should occur on a per stage basis if dependent
    on stage using a dictionary, or on a global basis if independent of stage.

    Please avoid referencing objects within this config from within a non pipeline
    component. This means these can be used from:

    - app.py
    - pipeline/pipeline_stack.py
    - pipeline/deployment_stage.py
    - pipeline/testing_setup/*

    The reason we are avoiding referencing objects here from within infrastructure
    constructs is that components should be reusable and should be parametrised
    by their input arguments rather than by outside configuration objects.


    ** Important **
    If you add a stage mapped parameter set, then please add it to the list of stage maps
    at the end of the file to test that all valid stages are present in the map.

    If a stage is added, please add it to the ValidStage enum and update all the stage maps
    to consider this parameter.

    See Also (optional)
    --------

    Testing config (more specifically) is available in pipeline/testing_setup/testing_config.py

    Examples (optional)
    --------
"""

class DeploymentType(str, Enum):
    # ProvenaConfig
    FULL_APP = "FULL_APP"
    # ProvenaUiOnlyConfig
    UI_ONLY = "UI_ONLY"

class ConfigSource(BaseModel):
    # What is the name of the config file to use for deployment - typically same as stage - don't include *.json postfix
    config_file_name: str
    # config source repo that defined this config
    repo_clone_string: str
    # The name space for the config
    namespace: str
    # The stage for the config
    stage: str
    # The secret ARN which contains the username/token combination to use for cloning the repo
    oauth_token_secret_arn: str
    # Which branch to use for the source config repo
    branch: str = "main"

class AWSTarget(BaseModel):
    account: str
    region: str

    @property
    def env(self) -> Environment:
        return Environment(account=self.account, region=self.region)

class Stage(str, Enum):
    TEST = "TEST"
    DEV = "DEV"
    STAGE = "STAGE"
    PROD = "PROD"

class ConfigBase(BaseModel):
    type: DeploymentType = DeploymentType.FULL_APP

    # Which application stage is this
    stage: Stage


"""
==================
APPLICATION CONFIG
==================
"""


class ProvenaComponent(str, Enum):
    NETWORKING = "NETWORKING"
    KEYCLOAK = "KEYCLOAK"
    IDENTITY_SERVICE = "IDENTITY_SERVICE"
    DATA_STORE = "DATA_STORE"
    LANDING_PAGE = "LANDING_PAGE"
    AUTH_API = "AUTH_API"
    SEARCH = "SEARCH"
    ASYNC_JOBS = "ASYNC_JOBS"
    ENTITY_REGISTRY = "ENTITY_REGISTRY"
    PROV_STORE = "PROV_STORE"
    WARMER = "WARMER"


class FeatName(BaseModel):
    ticket_num: int
    description: str


class SentryConfig(BaseModel):
    """
    A class used to represent the configuration for application monitoring via Sentry.

    Attributes
    ----------
    sentry_dsn_back_end : str, optional
        The Data Source Name (DSN) for the back-end Sentry service. If not provided, not events can be logged
    sentry_dsn_front_end : str, optional
        The Data Source Name (DSN) for the front-end Sentry service. If not provided, not events can be logged
    monitoring_enabled : bool, default=False
        A flag indicating whether monitoring is enabled for the entire application. If False, no events are logged.

    """

    sentry_dsn_back_end: Optional[str] = None
    sentry_dsn_front_end: Optional[str] = None
    monitoring_enabled: bool = False


"""
======
STAGES
======
"""


class NetworkingComponent(BaseModel):
    component: ProvenaComponent = ProvenaComponent.NETWORKING


class AsyncJobsComponent(BaseModel):
    job_api_domain: str

    job_api_extra_hash_dirs: List[str] = ASYNC_JOB_API_EXTRA_HASH_DIRS
    invoker_extra_hash_dirs: List[str] = ASYNC_INVOKER_EXTRA_HASH_DIRS
    connector_extra_hash_dirs: List[str] = ASYNC_CONNECTOR_EXTRA_HASH_DIRS

    # how long does the job poll before exiting (seconds)
    async_idle_timeout: int = 120

    # maximum number of concurrent tasks
    max_task_scaling: int = 3

    # Job config extra hash dirs (defaults provided)
    registry_job_extra_hash_dirs: List[str] = REGISTRY_JOB_EXTRA_HASH_DIRS
    prov_job_extra_hash_dirs: List[str] = PROV_JOB_EXTRA_HASH_DIRS
    email_job_extra_hash_dirs: List[str] = EMAIL_JOB_EXTRA_HASH_DIRS

    component: ProvenaComponent = ProvenaComponent.ASYNC_JOBS


class BackupType(str, Enum):
    # Put this into the critical plan - see Backup construct
    CRITICAL = "CRITICAL"
    # Put this into the non critical plan
    NON_CRITICAL = "NON_CRITICAL"
    # Put this into the special S3/data storage plan with PITR and monthly 3
    # month backups WARNING don't use this for non incremental storage types
    # such as dynamoDB as it will incur lots of storage costs
    DATA_STORAGE = "DATA_STORAGE"
    # Don't backup this resource
    NONE = "NONE"


class LambdaWarmerComponent(BaseModel):
    domain: str
    component: ProvenaComponent = ProvenaComponent.WARMER


class KeycloakConfiguration(BaseModel):
    # What should be displayed in the Login page etc
    display_name: str

    # What base URL should be used for the redirect URI configuration? no protocol or postfix e.g. google.com
    base_url: str

    # stage override - this overrides the stage realm config used - you can
    # choose to use dev KC setup with prod application, for example
    stage_override: Optional[Stage] = None


class KeycloakComponent(BaseModel):
    # auth domain
    domain: str

    # backup rds?
    rds_backup_policy: BackupType = BackupType.CRITICAL

    # Realm name e.g. "provena"
    realm_name: str

    # What is the name of the custom theme to inject?
    custom_theme_name: str = "default"

    # recover from snapshot?
    snapshot_arn: Optional[str] = None

    # if the snapshot is not provided, then the user must specify a set of
    # overrides for the default created realm config
    keycloak_configuration: Optional[KeycloakConfiguration] = None

    # rds removal policy
    rds_removal_policy: RemovalPolicy = RemovalPolicy.SNAPSHOT

    component: ProvenaComponent = ProvenaComponent.KEYCLOAK


class IdentityServiceComponent(BaseModel):
    handle_credentials_arn: str
    domain_name: str
    ardc_service_endpoint: str
    extra_hash_dirs: List[str] = DEFAULT_EXTRA_HASH_DIRS

    component: ProvenaComponent = ProvenaComponent.IDENTITY_SERVICE


class DataStoreComponent(BaseModel):
    # Service account creds for general API
    service_account_arn: str
    # Special service account for OIDC AWS connection
    oidc_service_account_arn: str

    # domains
    api_domain: str
    ui_domain: str

    extra_hash_dirs: List[str] = DEFAULT_EXTRA_HASH_DIRS

    component: ProvenaComponent = ProvenaComponent.DATA_STORE

    # default retain
    table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN


class LandingPageComponent(BaseModel):
    ui_domain: str
    component: ProvenaComponent = ProvenaComponent.LANDING_PAGE


class AuthApiComponent(BaseModel):
    api_domain: str

    extra_hash_dirs: List[str] = DEFAULT_EXTRA_HASH_DIRS

    pitr_request_table: bool = True
    pitr_groups_table: bool = True

    api_service_account_secret_arn: str
    access_alerts_email_address: str

    backup_request_table: BackupType = BackupType.NON_CRITICAL
    backup_groups_table: BackupType = BackupType.CRITICAL
    backup_username_person_link_table: BackupType = BackupType.CRITICAL

    # table removal policies
    request_table_removal_policy: RemovalPolicy = RemovalPolicy.DESTROY
    groups_table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN
    username_person_link_table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    component: ProvenaComponent = ProvenaComponent.AUTH_API


class SearchClusterEndpoints(BaseModel):
    domain_arn: str
    domain_endpoint: str


class SearchComponent(BaseModel):
    api_hash_dirs: List[str] = DEFAULT_EXTRA_HASH_DIRS
    streamer_extra_hash_dirs: List[str] = DEFAULT_EXTRA_HASH_DIRS

    # use an existing cluster!
    existing_cluster_info: Optional[SearchClusterEndpoints] = None

    # domains
    # cluster domain
    search_service_domain: Optional[str]

    # api domain
    api_domain: str

    # index names - these should be unique if sharing a cluster
    registry_index_name: str = "registry_index"
    global_index_name: str = "global_index"

    # streamer configurations
    stream_registry: bool = True  # requires entity-registry

    # open search removal policy
    cluster_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    # streamer linearised field name
    linearised_field_name: str = "body"

    component: ProvenaComponent = ProvenaComponent.SEARCH


class EntityRegistryComponent(BaseModel):
    # service account arn
    service_account_arn: str

    # hash config
    extra_hash_dirs: List[str] = REGISTRY_DEPENDANT_HASH_DIRS

    # domains
    api_domain: str
    ui_domain: str

    # backup
    pitr_enabled: bool = True
    tables_backup_policy: BackupType = BackupType.CRITICAL

    # removals
    tables_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    component: ProvenaComponent = ProvenaComponent.ENTITY_REGISTRY


class ProvStoreComponent(BaseModel):
    # deployment misc config
    prov_job_extra_hash_dirs: List[str] = PROV_JOB_EXTRA_HASH_DIRS
    extra_hash_dirs: List[str] = JOB_ENABLED_API_EXTRA_HASH_DIRS

    # domains
    api_domain: str
    ui_domain: str
    neo4j_http_domain: str
    neo4j_bolt_domain: str

    # secrets
    neo4j_auth_arn: str
    neo4j_memory_size: int
    neo4j_cpu_size: int
    service_account_arn: str
    neo4j_service_instance_role_arn: str
    prov_job_dispatcher_service_role_secret_arn: str

    # neo4j config
    neo4j_efs_root_path: str = "/"

    # neo4j backup policy
    efs_backup_policy: BackupType = BackupType.CRITICAL

    # default - retain EFS
    neo4j_efs_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    # job tables removal policies
    job_tables_removal_policy: RemovalPolicy = RemovalPolicy.DESTROY

    component: ProvenaComponent = ProvenaComponent.PROV_STORE


class ComponentConfig(BaseModel):
    # each component can either be included or not and defines a personal set of
    # config options
    networking: Optional[NetworkingComponent]
    keycloak: Optional[KeycloakComponent]
    identity_service: Optional[IdentityServiceComponent]
    data_store: Optional[DataStoreComponent]
    landing_page: Optional[LandingPageComponent]
    auth_api: Optional[AuthApiComponent]
    search: Optional[SearchComponent]
    entity_registry: Optional[EntityRegistryComponent]
    prov_store: Optional[ProvStoreComponent]
    warmer: Optional[LambdaWarmerComponent]
    async_jobs: Optional[AsyncJobsComponent]


"""
=============
DOMAIN CONFIG
=============
"""


class HZConfig(BaseModel):
    # this is the hosted zone name, usually the same as the root domain
    hosted_zone_name: str
    # this is the hosted zone ID
    hosted_zone_id: str


class DNSConfig(HZConfig):
    # awsregion specific certificate
    domain_certificate_arn: str
    # us-east-1 certificate for cloudfront
    us_east_certificate_arn: str


"""
=================
DEPLOYMENT CONFIG
=================
"""


class BuildBadgeConfig(BaseModel):
    build_domain: str
    interface_domain: str


class DeploymentConfig():
    config: ConfigSource

    # Stack IDs - used to specify what the stack names should be
    pipeline_stack_id: str
    deployment_stack_id: str

    # git owner/organisation e.g. provena
    git_owner_org: str
    # git repo name e.g. provena
    git_repo_name: str
    # Which git branch should the code be deployed from
    git_branch_name: str
    # git commit deploying from
    git_commit_id: Optional[str]
    git_commit_url: Optional[str]
    git_tag_name: Optional[str]
    git_release_title: Optional[str]
    git_release_url: Optional[str]

    # git repo string = owner_org/repo_name

    @property
    def git_repo_string(self) -> str:
        return f"{self.git_owner_org}/{self.git_repo_name}"

    # Which CDK target environment (account/region) should host the pipeline
    deployment_environment: AWSTarget
    # Which CDK target environment (account/region) should the application be deployed into
    pipeline_environment: AWSTarget
    # github oauth token arn
    github_token_arn: str

    # main pipeline trigger option
    main_pipeline_trigger: aws_codepipeline_actions.GitHubTrigger

    # cdk out path
    cdk_out_path: str

    # Sentry API monitoring?
    sentry_config: SentryConfig

    # Is this a feature branch deployment?
    feature_deployment: bool = False
    # If so - provide the ticket number
    ticket_number: Optional[int] = None

    # Should an interface export pipeline be deployed
    interface_pipeline: bool = True
    # Should a quick deploy pipeline be deployed
    quick_deploy_pipeline: bool = True
    # How should the pipeline be triggered?
    interface_pipeline_trigger_settings: Optional[
        aws_codepipeline_actions.GitHubTrigger
    ] = None
    # build badge?
    build_badge: Optional[BuildBadgeConfig] = None
    # Should a ui only pipeline be deployed
    ui_only_pipeline: bool = True
    # How should the pipeline be triggered?
    ui_pipeline_trigger_settings: Optional[aws_codepipeline_actions.GitHubTrigger] = (
        None
    )
    # Email alerts?
    email_alerts_activated: bool = True
    # What is the email address to send to?
    pipeline_alert_email: Optional[str] = None
    # Cross account deployment? I.e. set to true iff build account != deploy target
    cross_account: bool = False

    # code build jobs for tests triggered for PR -> this branch?
    ci_hook_pr_into_branch: bool = False

    # A set of account ids which should be able to build into static buckets
    trusted_ui_build_account_ids: Optional[List[str]] = None

    # synth command (generated from app name and output path)
    @property
    def cdk_input_output_subcommand(self) -> str:
        return f'--output "{self.cdk_out_path}"'

    # synth command (generated from app name and output path)
    @property
    def cdk_synth_command(self) -> str:
        env_vars: Dict[str, str] = {
            "PROVENA_CONFIG_ID": self.config.config_file_name,
        }

        if self.feature_deployment:
            if self.ticket_number is None:
                raise ValueError(
                    "Cannot deploy a feature stack without specifying the ticket number."
                )
            env_vars["TICKET_NUMBER"] = str(self.ticket_number)
            env_vars["BRANCH_NAME"] = self.git_branch_name

        if self.email_alerts_activated:
            env_vars["PIPELINE_ALERTS"] = "true"

        if self.sentry_config.monitoring_enabled:
            # note that because of how the config is set up,
            # the infra will interpret any non None value to be true
            env_vars["ENABLE_API_MONITORING"] = "true"

        export_string = " && ".join([f'export {k}="{v}"' for k, v in env_vars.items()])
        return f"{export_string} && npx cdk synth {self.cdk_input_output_subcommand}"


"""
==============
GENERAL CONFIG
==============
"""


class KeycloakEndpoints(BaseModel):
    full_endpoint: str
    minimal_endpoint: str
    issuer: str
    realm_name: str


class APIGatewayRateLimitingSettings(BaseModel):
    # Maximum number of concurrent requests which API gateway
    # can handle during immediate high traffic time periods
    throttling_burst_limit: int = 20

    # Rate limit controls the steady-state request rate, i.e., the
    # long-term average number of requests per second (RPS), which
    # API Gateway can handle. For example, if a rate limit of 500 is
    # set, it means API Gateway will be able to process 500 requests
    # per second on an average over a long period.
    throttling_rate_limit: int = 10


class GeneralConfig(BaseModel):
    email_connection_secret_arn: str

    # used for authenticating docker pulls
    dockerhub_creds_arn: str

    # storage bucket arn and backup
    storage_bucket_arn: str
    storage_bucket_backup_policy: BackupType = BackupType.NONE

    # what is the root domain of the application (not necessarily same as hosted zone)
    # e.g. dev.provena.io
    root_domain: str

    # What theme ID is used for the UIs?
    ui_theme_id: str = "default"

    # Links for deployment specific documentation/contact us links
    documentation_base_link: str
    contact_us_link: str

    # Rate limiting setup for API Gateways
    rate_limiting: Optional[APIGatewayRateLimitingSettings] = None

    # if keycloak is not deployed, ensure these are present
    keycloak_endpoints: Optional[KeycloakEndpoints] = None

    # extra name prefix - prefixes an extra name to some resources if required
    extra_name_prefix: Optional[str] = None

    # These tags will be added to the whole application tree
    tags: Optional[Dict[str, str]] = None


class TestType(str, Enum):
    TS_TYPE_CHECK = "TS_TYPE_CHECK"
    MYPY_TYPE_CHECK = "MYPY_TYPE_CHECK"
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    SYSTEM = "SYSTEM"


class UnitTestConfig(BaseModel):
    handle_secret_arn: str
    ardc_service_endpoint: str = "https://demo.identifiers.ardc.edu.au/pids"


class IntegrationTestConfig(BaseModel):
    keycloak_client_id: str
    # data_store_user_creds_arn: str
    # registry_user_creds_arn: str
    integration_test_bots_creds_arn: str


class SystemTestConfig(BaseModel):
    shared_link: str
    user_creds_arn: str


class TestConfig(BaseModel):
    # which tests should be run in the deployed pipeline?
    test_activation: Dict[TestType, bool]

    unit_tests: Optional[UnitTestConfig]
    integration_tests: Optional[IntegrationTestConfig]
    system_tests: Optional[SystemTestConfig] = None


# ======
# BACKUP
# ======


class BackupConfig(BaseModel):
    # Backups switched on? Settings below will be ignored if set to False
    backups_enabled: bool

    # Is there an existing vault to put plans into?
    existing_vault_arn: Optional[str] = None

    # Provide a custom vault name? It is good to provide a custom name because
    # the cloudformation engine does not like replacing the resource since it is
    # by default a custom named resource. If replacement is required - easiest
    # to just change this name in the same changeset to force a new vault.
    vault_name: Optional[str] = None

    # The below properties cannot be provided if an existing vault is to be used

    # Key admins if required default = [] -> specify inputs to ArnPrincipal
    key_admins: Optional[List[str]] = None

    # Trusted vault accounts (copy into this one) - these will have the vault
    # access policy which enables copies from this vault
    trusted_copy_source_account_ids: Optional[List[str]] = None

    # Which accounts do we want to be able to copy to - these will have the KMS
    # key shared at an account level with these account IDs
    trusted_copy_destination_account_ids: Optional[List[str]] = None


"""
==========
ALL CONFIG
==========
"""


class ProvenaConfig(ConfigBase):
    # type inherited from base
    deployment: DeploymentConfig
    components: ComponentConfig
    tests: TestConfig
    general: GeneralConfig
    dns: DNSConfig
    backup: BackupConfig


class ResolvedDomainNames(BaseModel):
    # e.g. provena.io
    root_domain: str

    # APIs (full e.g. https://...com)
    data_store_api: str
    prov_api: str
    registry_api: str
    search_api: str
    auth_api: str
    warmer_api: str
    async_jobs_api: str

    # UIs (full e.g. https://...com)
    data_store_ui: str
    prov_ui: str
    landing_ui: str
    registry_ui: str

    # Other
    # e.g. https://auth.dev.provena.io/auth
    keycloak_minimal: str
    keycloak_realm_name: str


class UiOnlyDomainNames(BaseModel):
    # this is a static representation of all non ui domains in the system
    root_domain: str
    landing_page_sub_domain: str
    registry_sub_domain: str
    data_store_sub_domain: str
    prov_store_sub_domain: str

    search_api_endpoint: str
    prov_api_endpoint: str
    data_api_endpoint: str
    auth_api_endpoint: str
    registry_api_endpoint: str
    warmer_api_endpoint: str
    async_jobs_api_endpoint: str

    documentation_base_link: str
    contact_us_link: str

    keycloak_minimal_endpoint: str
    keycloak_realm_name: str


class ProvenaUIOnlyConfig(ConfigBase):
    config: ConfigSource
    # Stack IDs - used to specify what the stack names should be
    pipeline_stack_id: str
    deployment_stack_id: str

    github_token_arn: str

    # used for authenticating docker pulls
    dockerhub_creds_arn: str

    git_repo_name: str
    git_owner_org: str
    git_branch_name: str
    git_commit_id: Optional[str]

    # git repo string = owner_org/repo_name
    @property
    def git_repo_string(self) -> str:
        return f"{self.git_owner_org}/{self.git_repo_name}"

    aws_environment: AWSTarget
    domains: UiOnlyDomainNames
    dns: DNSConfig

    # What theme ID is used for the UIs?
    ui_theme_id: str = "default"

    cdk_out_path: str
    ticket_number: int

    sentry_config: SentryConfig

    email_alerts_activated: bool
    pipeline_alert_email: Optional[str] = None

    # synth command (generated from app name and output path)
    @property
    def cdk_input_output_subcommand(self) -> str:
        return f'--output "{self.cdk_out_path}"'

    # synth command (generated from app name and output path)
    @property
    def cdk_synth_command(self) -> str:
        env_vars: Dict[str, str] = {
            "PROVENA_CONFIG_ID": self.config.config_file_name,
            "TICKET_NUMBER": str(self.ticket_number),
            "BRANCH_NAME": self.git_branch_name,
        }

        if self.sentry_config.monitoring_enabled:
            # note that because of how the config is set up,
            # the infra will interpret any non None value to be true
            env_vars["ENABLE_API_MONITORING"] = "true"

        if self.email_alerts_activated:
            env_vars["PIPELINE_ALERTS"] = "true"

        export_string = " && ".join([f'export {k}="{v}"' for k, v in env_vars.items()])

        return f"{export_string} && npx cdk synth {self.cdk_input_output_subcommand}"