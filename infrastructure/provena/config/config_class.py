from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from aws_cdk import (
    Environment,
    aws_codepipeline_actions,
    aws_iam as iam,
    RemovalPolicy
)
from typing import Any, List
from enum import Enum, auto

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


class Stage(str, Enum):
    TEST = "TEST"
    DEV = "DEV"
    STAGE = "STAGE"
    PROD = "PROD"


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
    ENTITY_REGISTRY = "ENTITY_REGISTRY"
    PROV_STORE = "PROV_STORE"
    WARMER = "WARMER"


@dataclass
class FeatName:
    ticket_num: int
    description: str


"""
======
STAGES
======
"""


@dataclass
class NetworkingComponent():
    component: ProvenaComponent = ProvenaComponent.NETWORKING


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


@dataclass
class LambdaWarmerComponent():
    domain: str
    component: ProvenaComponent = ProvenaComponent.WARMER


@dataclass
class KeycloakConfiguration():
    # realm name is already known

    # What should be displayed in the Login page etc
    display_name: str

    # What base URL should be used for the redirect URI configuration? no protocol or postfix e.g. google.com
    base_url: str

    # stage override - this overrides the stage realm config used - you can
    # choose to use dev KC setup with prod application, for example
    stage_override: Optional[Stage] = None


@dataclass
class KeycloakComponent():
    # auth domain
    domain: str

    # backup rds?
    rds_backup_policy: BackupType

    # Realm name e.g. "provena"
    realm_name: str

    # What is the name of the custom theme to inject?
    custom_theme_name: str

    # recover from snapshot?
    snapshot_arn: Optional[str] = None

    # if the snapshot is not provided, then the user must specify a set of
    # overrides for the default created realm config
    keycloak_configuration: Optional[KeycloakConfiguration] = None

    # rds removal policy
    rds_removal_policy: RemovalPolicy = RemovalPolicy.SNAPSHOT

    component: ProvenaComponent = ProvenaComponent.KEYCLOAK


@dataclass
class IdentityServiceComponent():
    handle_credentials_arn: str
    domain_name: str
    ardc_service_endpoint: str
    extra_hash_dirs: List[str]

    component: ProvenaComponent = ProvenaComponent.IDENTITY_SERVICE


@dataclass
class DataStoreComponent():
    # Service account creds for general API
    service_account_arn: str
    # Special service account for OIDC AWS connection
    oidc_service_account_arn: str

    # domains
    api_domain: str
    ui_domain: str

    # backup
    pitr_enabled: bool
    table_backup_policy: BackupType

    extra_hash_dirs: List[str]

    component: ProvenaComponent = ProvenaComponent.DATA_STORE

    # default retain
    table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN


@dataclass
class LandingPageComponent():
    ui_domain: str
    component: ProvenaComponent = ProvenaComponent.LANDING_PAGE


@dataclass
class AuthApiComponent():
    extra_hash_dirs: List[str]

    pitr_request_table: bool
    pitr_groups_table: bool

    backup_request_table: BackupType
    backup_groups_table: BackupType
    backup_username_person_link_table: BackupType

    api_domain: str

    # table removal policies
    request_table_removal_policy: RemovalPolicy = RemovalPolicy.DESTROY
    groups_table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN
    username_person_link_table_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    component: ProvenaComponent = ProvenaComponent.AUTH_API


@dataclass
class SearchClusterEndpoints():
    domain_arn: str
    domain_endpoint: str


@dataclass
class SearchComponent():
    api_hash_dirs: List[str]
    streamer_extra_hash_dirs: List[str]

    # use an existing cluster!
    existing_cluster_info: Optional[SearchClusterEndpoints]

    # domains
    # cluster domain
    search_service_domain: Optional[str]

    # api domain
    api_domain: str

    # index names - these should be unique if sharing a cluster
    registry_index_name: str
    global_index_name: str

    # streamer configurations
    stream_registry: bool  # requires entity-registry

    # open search removal policy
    cluster_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    # streamer linearised field name
    linearised_field_name: str = "body"

    component: ProvenaComponent = ProvenaComponent.SEARCH


@dataclass
class EntityRegistryComponent():
    # service account arn
    service_account_arn: str

    # hash config
    extra_hash_dirs: List[str]

    # domains
    api_domain: str
    ui_domain: str

    # backup
    pitr_enabled: bool
    tables_backup_policy: BackupType

    # removals
    tables_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    component: ProvenaComponent = ProvenaComponent.ENTITY_REGISTRY


@dataclass
class ProvStoreComponent():
    # deployment misc config
    prov_job_extra_hash_dirs: List[str]
    extra_hash_dirs: List[str]

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
    neo4j_efs_root_path: str

    # neo4j backup policy
    efs_backup_policy: BackupType

    # default - retain EFS
    neo4j_efs_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN

    # job tables removal policies
    job_tables_removal_policy: RemovalPolicy = RemovalPolicy.DESTROY

    component: ProvenaComponent = ProvenaComponent.PROV_STORE


@ dataclass
class ComponentConfig():
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


"""
=============
DOMAIN CONFIG
=============
"""


@dataclass
class HZConfig():
    # this is the root domain to which the component config domains will be
    # relative to
    root_domain: str
    # this is the hosted zone name, usually the same as the root domain
    hosted_zone_name: str
    # this is the hosted zone ID
    hosted_zone_id: str


@ dataclass
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


@dataclass
class BuildBadgeConfig():
    build_domain: str
    interface_domain: str


@dataclass
class DeploymentConfig():
    # What is the Provena config ID of this config?
    config_id: str

    # Stack IDs - used to specify what the stack names should be
    pipeline_stack_id: str
    deployment_stack_id: str

    # Which application stage is this
    stage: Stage

    # git owner/organisation e.g. provena
    git_owner_org: str
    # git repo name e.g. provena
    git_repo_name: str
    # Which git branch should the code be deployed from
    git_branch_name: str

    # git repo string = owner_org/repo_name
    @property
    def git_repo_string(self) -> str:
        return f"{self.git_owner_org}/{self.git_repo_name}"

    # Which CDK target environment (account/region) should host the pipeline
    deployment_environment: Environment
    # Which CDK target environment (account/region) should the application be deployed into
    pipeline_environment: Environment
    # github oauth token arn
    github_token_arn: str

    # main pipeline trigger option
    main_pipeline_trigger: aws_codepipeline_actions.GitHubTrigger

    # cdk out path
    cdk_out_path: str
    # The name of the cdk python app
    cdk_app_name: str

    # Is this a feature branch deployment?
    feature_deployment: bool = False
    # If so - provide the ticket number
    ticket_no: Optional[int] = None

    # Should an interface export pipeline be deployed
    interface_pipeline: bool = True
    # How should the pipeline be triggered?
    interface_pipeline_trigger_settings: Optional[aws_codepipeline_actions.GitHubTrigger] = None
    # build badge?
    build_badge: Optional[BuildBadgeConfig] = None
    # Should a ui only pipeline be deployed
    ui_only_pipeline: bool = True
    # How should the pipeline be triggered?
    ui_pipeline_trigger_settings: Optional[aws_codepipeline_actions.GitHubTrigger] = None
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
        return f'--app "python {self.cdk_app_name}" --output "{self.cdk_out_path}"'

    # synth command (generated from app name and output path)
    @property
    def cdk_synth_command(self) -> str:
        if not self.feature_deployment:
            return f'export PROVENA_CONFIG_ID="{self.config_id}" && npx cdk synth {self.cdk_input_output_subcommand}'
        else:
            if self.ticket_no is None:
                raise ValueError(
                    "Cannot deploy a feature stack without specifying the ticket number.")

            return f'export BRANCH_NAME="{self.git_branch_name}" && export TICKET_NO="{self.ticket_no}" && export PROVENA_CONFIG_ID="{self.config_id}" && npx cdk synth {self.cdk_input_output_subcommand}'


"""
==============
GENERAL CONFIG
==============
"""


@dataclass
class KeycloakEndpoints():
    full_endpoint: str
    minimal_endpoint: str
    issuer: str
    realm_name: str


@dataclass
class GeneralConfig():
    email_connection_secret_arn: str
    dockerhub_creds_arn: str

    # storage bucket arn and backup
    storage_bucket_arn: str
    storage_bucket_backup_policy: BackupType

    # what is the root domain of the application (not necessarily same as hosted zone)
    # e.g. dev.provena.io
    application_root_domain: str

    # What theme ID is used for the UIs?
    ui_theme_id: str
    
    # Links for deployment specific documentation/contact us links
    documentation_base_link: str
    contact_us_link: str

    # if keycloak is not deployed, ensure these are present
    keycloak_endpoints: Optional[KeycloakEndpoints] = None

    # extra name prefix - prefixes an extra name to some resources if required
    extra_name_prefix: Optional[str] = None

    # These tags will be added to the whole application tree
    tags: Dict[str, str] = field(default_factory=lambda: {})


class TestType(str, Enum):
    TS_TYPE_CHECK = auto()
    MYPY_TYPE_CHECK = auto()
    UNIT = auto()
    INTEGRATION = auto()
    SYSTEM = auto()


@dataclass
class UnitTestConfig():
    handle_secret_arn: str
    ardc_service_endpoint: str


@dataclass
class IntegrationTestConfig():
    keycloak_client_id: str
    # data_store_user_creds_arn: str
    # registry_user_creds_arn: str
    integration_test_bots_creds_arn: str


@dataclass
class SystemTestConfig():
    shared_link: str
    user_creds_arn: str


@dataclass
class TestConfig():
    # which tests should be run in the deployed pipeline?
    test_activation: Dict[TestType, bool]

    unit_tests: Optional[UnitTestConfig]
    integration_tests: Optional[IntegrationTestConfig]
    system_tests: Optional[SystemTestConfig]


# ======
# BACKUP
# ======

@dataclass
class BackupConfig():
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

    # Key admins if required
    key_admins: List[iam.IPrincipal] = field(default_factory=lambda: [])

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


@ dataclass
class ProvenaConfig():
    deployment: DeploymentConfig
    components: ComponentConfig
    tests: TestConfig
    general: GeneralConfig
    dns: DNSConfig
    backup: BackupConfig


@dataclass
class ResolvedDomainNames():
    # e.g. provena.io
    root_domain: str

    # APIs (full e.g. https://...com)
    data_store_api: str
    prov_api: str
    registry_api: str
    search_api: str
    auth_api: str
    warmer_api: str

    # UIs (full e.g. https://...com)
    data_store_ui: str
    prov_ui: str
    landing_ui: str
    registry_ui: str

    # Other
    # e.g. https://auth.dev.provena.io/auth
    keycloak_minimal: str
    keycloak_realm_name: str


@dataclass
class UiOnlyDomainNames():
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

    documentation_base_link: str
    contact_us_link: str

    keycloak_minimal_endpoint: str
    keycloak_realm_name: str


@ dataclass
class ProvenaUIOnlyConfig():
    # What is the provena config ID of this deployment
    config_id: str

    # Stack IDs - used to specify what the stack names should be
    pipeline_stack_id: str
    deployment_stack_id: str

    github_token_arn: str

    git_repo_name: str
    git_owner_org: str
    git_branch_name: str

    # git repo string = owner_org/repo_name
    @property
    def git_repo_string(self) -> str:
        return f"{self.git_owner_org}/{self.git_repo_name}"

    aws_environment: Environment
    target_stage: Stage
    domains: UiOnlyDomainNames
    dns: DNSConfig
    
    # What theme ID is used for the UIs?
    ui_theme_id: str
    
    cdk_out_path: str
    cdk_app_name: str
    ticket_no: int
    email_alerts_activated: bool
    pipeline_alert_email: Optional[str] = None

    # synth command (generated from app name and output path)
    @property
    def cdk_input_output_subcommand(self) -> str:
        return f'--app "python {self.cdk_app_name}" --output "{self.cdk_out_path}"'

    # synth command (generated from app name and output path)
    @property
    def cdk_synth_command(self) -> str:
        return f'{"export PIPELINE_ALERTS=true && " if self.email_alerts_activated else ""}export BRANCH_NAME="{self.git_branch_name}" && export TICKET_NO="{self.ticket_no}" && export PROVENA_CONFIG_ID="{self.config_id}" && npx cdk synth {self.cdk_input_output_subcommand}'


@dataclass
class GithubBootstrapConfig():
    env: Environment
    github_token_arn: str
