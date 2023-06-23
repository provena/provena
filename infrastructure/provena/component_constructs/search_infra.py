from aws_cdk import (
    aws_opensearchservice as search,
    aws_certificatemanager as acm,
    aws_route53 as r53,
    RemovalPolicy,
    Fn
)

from constructs import Construct
from typing import Any, Optional


class OpenSearchCluster(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            cert_arn: str,
            hz: r53.IHostedZone,
            removal_policy: RemovalPolicy,
            # if creating a new domain
            search_domain: Optional[str],
            # if sharing an existing one
            existing_domain_arn: Optional[str] = None,
            existing_domain_endpoint: Optional[str] = None,
            instance_type: str = "t3.medium.search",
            version: search.EngineVersion = search.EngineVersion.OPENSEARCH_1_3,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        domain: search.IDomain

        if existing_domain_arn is None:
            assert search_domain

            # fully qualified domain name
            qualified_domain_name = f"{search_domain}.{hz.zone_name}"

            # setup an open search cluster
            # this is a prototyping setup TODO encryption, auth, VPC? etc
            domain = search.Domain(
                scope=self,
                id='domain',
                version=version,
                removal_policy=removal_policy,
                capacity=search.CapacityConfig(
                    data_nodes=1,
                    # search node 1xr5.large (default)
                    data_node_instance_type=instance_type,
                    master_nodes=0,
                    warm_nodes=0
                ),
                # This will add the Cname record for us
                custom_endpoint=search.CustomEndpointOptions(
                    # domain name relative to the hosted zone
                    domain_name=qualified_domain_name,
                    certificate=acm.Certificate.from_certificate_arn(
                        scope=self,
                        id='cert',
                        certificate_arn=cert_arn,
                    ),
                    hosted_zone=hz
                ),
                # only https allowed
                enforce_https=True
            )
        else:
            assert existing_domain_endpoint
            domain = search.Domain.from_domain_attributes(
                scope=self,
                id='domain',
                domain_arn=existing_domain_arn,
                domain_endpoint=existing_domain_endpoint
            )

        # expose the domain
        self.domain = domain

        # expose the endpoint - output depends on if sharing search cluster

        if existing_domain_arn is None:
            # construct the domains - this uses a custom endpoint
            self.qualified_domain_endpoint = f"https://{search_domain}.{hz.zone_name}"
            self.unqualified_domain_endpoint = f"{search_domain}.{hz.zone_name}"
        else:
            # this uses the provided domain endpoint - probably a default generated endpoint
            assert existing_domain_endpoint
            assert existing_domain_arn
            assert existing_domain_endpoint.startswith("https://")

            # full version
            self.qualified_domain_endpoint = existing_domain_endpoint

            # non https version
            self.unqualified_domain_endpoint = existing_domain_endpoint[8:]
