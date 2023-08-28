from constructs import Construct
from aws_cdk import (
    Stage as CdkStage,
    CfnOutput
)
from provena.provena_stack import ProvenaStack
from provena.ui_only_provena_stack import ProvenaUIStack
from provena.config.config_class import *


class ProvenaDeploymentStage(CdkStage):
    def deploy_stage(self, config: ProvenaConfig) -> None:
        """    deploy_stage
            Generates the actual deployment infrastructure based on
            extensive stage parameterised configuration in the config.py 
            top level config.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """

        # Potential apex entry - so consider this before
        # forming landing portal URL

        self.landing_portal_url: Optional[str] = None
        if config.components.landing_page:
            # deploying landing portal
            landing_ui_domain = config.components.landing_page.ui_domain
            if (landing_ui_domain == ""):
                self.landing_portal_url = f"https://{config.dns.root_domain}"
            else:
                self.landing_portal_url = f"https://{landing_ui_domain}.{config.dns.root_domain}"

        # data store url
        self.data_store_url: Optional[str] = None

        if config.components.data_store:
            self.data_store_url = f"https://{config.components.data_store.ui_domain}.{config.dns.root_domain}"

        # prov store url
        self.prov_store_url: Optional[str] = None

        if config.components.prov_store:
            self.prov_store_url = f"https://{config.components.prov_store.ui_domain}.{config.dns.root_domain}"

        # registry url
        self.registry_url: Optional[str] = None

        if config.components.entity_registry:
            self.registry_url = f"https://{config.components.entity_registry.ui_domain}.{config.dns.root_domain}"

        self.infra = ProvenaStack(
            scope=self,
            id=config.deployment.deployment_stack_id,
            env=config.deployment.deployment_environment,
            config=config
        )

    def __init__(self, scope: Construct, id: str, config: ProvenaConfig, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        self.stack_prefix = id
        self.deploy_stage(config=config)

        # cfn outputs
        self.data_store_ui_bucket_name: CfnOutput = self.infra.data_store_ui_bucket_name
        self.data_api_endpoint: CfnOutput = self.infra.data_api_endpoint
        self.job_api_endpoint: CfnOutput = self.infra.job_api_endpoint
        self.registry_api_endpoint: CfnOutput = self.infra.registry_api_endpoint
        self.registry_ui_bucket_name: CfnOutput = self.infra.registry_ui_bucket_name
        self.prov_ui_bucket_name: CfnOutput = self.infra.prov_ui_bucket_name
        self.prov_api_endpoint: CfnOutput = self.infra.prov_api_endpoint
        self.search_api_endpoint: CfnOutput = self.infra.search_api_endpoint
        self.auth_api_endpoint: CfnOutput = self.infra.auth_api_endpoint
        self.landing_page_ui_bucket_name: CfnOutput = self.infra.landing_page_ui_bucket_name
        self.keycloak_auth_endpoint_minimal_cfn_output: CfnOutput = self.infra.keycloak_auth_endpoint_minimal_cfn
        self.keycloak_auth_endpoint_cfn_output: CfnOutput = self.infra.keycloak_auth_endpoint_cfn
        self.warmer_api_endpoint: CfnOutput = self.infra.warmer_api_endpoint


class ProvenaUIOnlyStage(CdkStage):
    def deploy_stage(self, config: ProvenaUIOnlyConfig) -> None:
        """    deploy_stage
            Generates the actual deployment infrastructure based on
            extensive stage parameterised configuration in the config.py 
            top level config.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        self.infra = ProvenaUIStack(
            scope=self,
            construct_id=config.deployment_stack_id,
            env=config.aws_environment,
            config=config
        )

    def __init__(self, scope: Construct, id: str, config: ProvenaUIOnlyConfig, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        self.stack_prefix = id
        self.deploy_stage(config=config)

        # cfn outputs
        self.data_store_ui_bucket_name: CfnOutput = self.infra.data_store_ui_bucket_name
        self.registry_ui_bucket_name: CfnOutput = self.infra.registry_ui_bucket_name
        self.prov_ui_bucket_name: CfnOutput = self.infra.prov_ui_bucket_name
        self.landing_page_ui_bucket_name: CfnOutput = self.infra.landing_page_ui_bucket_name
