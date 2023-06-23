from aws_cdk import (
    Stack,
    CfnOutput,
)
from constructs import Construct
from provena.component_constructs.static_cloudfront_distribution import StaticCloudfrontDistribution
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.config.config_class import ProvenaUIOnlyConfig
from typing import Any, List


def get_priority(used_priorities: List[int]) -> int:
    priority = max(used_priorities) + 1
    used_priorities.append(priority)
    return priority


class ProvenaUIStack(Stack):
    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 config: ProvenaUIOnlyConfig,
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # pull out some common vars
        stage = config.target_stage
        us_east_cert_arn = config.dns.us_east_certificate_arn

        # Create allocator to use
        dns_allocator = DNSAllocator(
            scope=self,
            construct_id="dns",
            hosted_zone_id=config.dns.hosted_zone_id,
            hosted_zone_name=config.dns.hosted_zone_name
        )

        landing_page_ui = StaticCloudfrontDistribution(
            scope=self,
            construct_id="landing-page-ui",
            stage=stage,
            us_east_cert_arn=us_east_cert_arn,
            sub_domain=config.domains.landing_page_sub_domain,
            root_domain=config.domains.root_domain,
            dns_allocator=dns_allocator)

        self.landing_page_ui_bucket_name = CfnOutput(
            scope=self,
            id="landing_page_ui_bucket_name",
            value=landing_page_ui.bucket_name)

        registry_ui = StaticCloudfrontDistribution(
            scope=self,
            construct_id="registry-ui",
            stage=stage,
            us_east_cert_arn=us_east_cert_arn,
            sub_domain=config.domains.registry_sub_domain,
            root_domain=config.domains.root_domain,
            dns_allocator=dns_allocator
        )

        self.registry_ui_bucket_name = CfnOutput(
            scope=self,
            id="registry_ui_bucket_name",
            value=registry_ui.bucket_name)

        ds_ui = StaticCloudfrontDistribution(
            scope=self,
            construct_id="data-store-ui",
            stage=stage,
            us_east_cert_arn=us_east_cert_arn,
            sub_domain=config.domains.data_store_sub_domain,
            root_domain=config.domains.root_domain,
            dns_allocator=dns_allocator,
        )

        self.data_store_ui_bucket_name = CfnOutput(
            scope=self,
            id="data_store_ui_bucket_name",
            value=ds_ui.bucket_name)

        prov_ui = StaticCloudfrontDistribution(
            scope=self,
            construct_id="prov-ui",
            stage=stage,
            us_east_cert_arn=us_east_cert_arn,
            sub_domain=config.domains.prov_store_sub_domain,
            root_domain=config.domains.root_domain,
            dns_allocator=dns_allocator)

        self.prov_ui_bucket_name = CfnOutput(
            scope=self,
            id="prov_ui_bucket_name",
            value=prov_ui.bucket_name)
