# from aws_cdk import (
# )
from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.static_cloudfront_s3_website import StaticCloudfrontS3Website
from provena.custom_constructs.storage_bucket import StaticWebsiteBucket
from typing import Any, Optional, List


class StaticCloudfrontDistribution(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 stage: str,
                 us_east_cert_arn: str,
                 sub_domain: str,  # e.g. static or "" for apex
                 root_domain: str,  # e.g. provena.io
                 dns_allocator: DNSAllocator,  # the dns allocator object
                 trusted_build_accounts: Optional[List[str]] = None,
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Setup storage bucket
        static_website_bucket = StaticWebsiteBucket(
            scope=self,
            construct_id='bucket',
            trusted_build_account_ids=trusted_build_accounts
        )

        # expose bucket name
        self.bucket_name = static_website_bucket.bucket.bucket_name

        # Create cloudfront distribution
        distribution = StaticCloudfrontS3Website(self,
                                                 construct_id=construct_id + '-dist',
                                                 bucket=static_website_bucket.bucket,
                                                 sub_domain=sub_domain,
                                                 root_domain=root_domain,
                                                 cert_arn=us_east_cert_arn,
                                                 dns_allocator=dns_allocator
                                                 )