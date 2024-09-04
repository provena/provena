
from aws_cdk import (
    Duration,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
)
from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from typing import Any


class StaticCloudfrontS3Website(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 bucket: s3.Bucket,
                 sub_domain: str,
                 root_domain: str,
                 cert_arn: str,
                 dns_allocator: DNSAllocator,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        self.distribution = cloudfront.Distribution(scope=self,
                                                    id="dist",
                                                    default_behavior=cloudfront.BehaviorOptions(
                                                        origin=origins.S3Origin(
                                                            bucket=bucket,
                                                        ),
                                                        # TODO change this for PROD
                                                        # currently disables all caching but we should
                                                        # enable cloudfront caching for PROD
                                                        cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                                                        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                                                    ),
                                                    # us-east-1 cert
                                                    certificate=acm.Certificate.from_certificate_arn(
                                                        self, "cert", cert_arn),
                                                    default_root_object='index.html',

                                                    # Create apex entry if empty string otherwise prepended with delimiter
                                                    # also add the www. redirect domain to alternate
                                                    # domains
                                                    domain_names=[f"{sub_domain}.{root_domain}"] if sub_domain != "" else [
                                                        root_domain,
                                                        f"www.{root_domain}"
                                                    ],
                                                    enabled=True,
                                                    error_responses=[cloudfront.ErrorResponse(
                                                        http_status=404,
                                                        response_http_status=200,
                                                        response_page_path='/index.html',
                                                        ttl=Duration.days(1)
                                                    ),
                                                        cloudfront.ErrorResponse(
                                                        http_status=403,
                                                        response_http_status=200,
                                                        response_page_path='/index.html',
                                                        ttl=Duration.days(1)
                                                    )
                                                    ]
                                                    )
        # Adds a new record to the hosted zone (or updates current one)

        # If the domain name is an empty string then flag this as apex entry

        if sub_domain == "":

            # Add Alias A record at apex to cloudfront (unique)
            dns_allocator.add_apex_cloudfront_distribution_target(
                construct_id + 'apex-cloudfront-dns',
                target=self.distribution
            )

            # Add cname redirect from www -> apex for browsers which auto
            # prepend www.
            # This needs to be unique within the hosted zone
            # since this is not unique in any way
            dns_allocator.add_subdomain_redirect(
                id=construct_id + 'www-redirect',
                from_domain='www',
                to_domain="",
                comment=f"Adding redirect from www to {dns_allocator.root_domain}"
            )
        else:
            dns_allocator.add_cloudfront_distribution_target(
                construct_id + '-cloudfront-dns',
                domain=sub_domain,
                target=self.distribution
            )
