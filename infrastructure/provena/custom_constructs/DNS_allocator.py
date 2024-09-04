from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_route53_targets as r53_targets,
    aws_route53 as r53,
    aws_apigateway as api_gw,
    aws_cloudfront as cloudfront,
    Duration
)
from constructs import Construct

from typing import Optional, Any

# How long should the dns leases last, by default?
DEFAULT_TTL = Duration.minutes(15)


class DNSAllocator(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 hosted_zone_name: str,
                 hosted_zone_id: str,
                 root_domain: str,
                 **kwargs: Any) -> None:
        """A construct which enables the dynamic subscription
        of ec2 instances with elastic IPs and statically hosted
        s3 buckets to a route53 hosted zone. Also can attach to 
        elastic application load balancer targets.

        Args:
            scope (cdk.Construct): The surrounding CDK object.
            construct_id (str): The CDK id.
            zone_domain_name (str): The name of the hosted zone (domain name)
            hosted_zone_id (str): The hosted zone id (fixed)
        """

        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # the application root domain which routes will be respective to 
        self.root_domain = root_domain 

        # Pull the existing Hosted Zone based on the hosted_zone_id
        self.hz = r53.PublicHostedZone.from_hosted_zone_attributes(
            scope=self,
            id=construct_id + "_hosted_zone",
            hosted_zone_id=hosted_zone_id,
            zone_name=hosted_zone_name
        )

    def add_instance(self,
                     id: str,
                     domain_prefix: str,
                     target_eip: ec2.CfnEIP,
                     comment: Optional[str] = None,
                     route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        """Given some information, links the elastic IP of an ec2 instance
        to a specified domain prefix on the given hosted zone.

        Args:
            id (str): The CDK id of the record you are creating (your choice)
            domain_prefix (str): The prefix (excluding the full stop) of the
            target e.g. if you want api.example.com and the domain is example.com,
            you should include "api."
            target_eip (ec2.CfnEIP): The elastic IP associated to the ec2 instance.
            comment (Optional[str], optional): A comment to tie to the record.
            Defaults to None.
            route_ttl (Optional[Duration], optional): The time to live of the DNS result.
            Defaults to DEFAULT_TTL.
        """
        # Adds a new record to the hosted zone (or updates current one)
        r53.ARecord(
            scope=self,
            id=id,
            zone=self.hz,
            record_name=f"{domain_prefix}.{self.root_domain}.",
            comment=comment,
            ttl=route_ttl,
            # This is the only way to get the elastic IP to resolve
            # properly - no idea why this works?
            # I think cloud formation is BTS resolving the reference to the
            # newest IP. If you use the public_ip field of the ec2 instance, it is
            # not usually correct.
            target=r53.RecordTarget.from_ip_addresses(target_eip.ref)
        )

    def add_static_website(self,
                           id: str,
                           unqualified_bucket_name: str,
                           comment: Optional[str] = None,
                           route_ttl: Optional[Duration] = DEFAULT_TTL,
                           region: Optional[str] = "ap-southeast-2") -> None:
        """Links a static s3 bucket website to the provided hosted zone.

        Args:
            id (str): The CDK id of the record (your choice)
            unqualified_bucket_name (str): The name of the bucket itself (without domain info.) E.g.
            if you had a bucket named api but it was part of the domain my.app.com just provide
            api, even though the bucket's full name was forced to be api.my.app.com.
            comment (Optional[str], optional): Comment for the record. Defaults to None.
            route_ttl (Optional[Duration], optional): Time to live of DNS record. Defaults to DEFAULT_TTL.
            region (Optional[str], optional): The bucket region. Defaults to "ap-southeast-2".
        """

        # Work out the full qualified domain name
        full_domain_target = f"{unqualified_bucket_name}.{self.root_domain}.s3-website-{region}.amazonaws.com"

        # Name of the record (desired URL) must be the qualified bucket name
        record_name = f"{unqualified_bucket_name}.{self.root_domain}."

        # Create the record
        r53.CnameRecord(
            scope=self,
            id=id,
            domain_name=full_domain_target,
            record_name=record_name,
            ttl=route_ttl,
            zone=self.hz,
            comment=comment
        )

    def add_load_balancer(self,
                          id: str,
                          domain_prefix: str,
                          load_balancer: elb.ILoadBalancerV2,
                          comment: Optional[str] = None,
                          route_ttl: Optional[Duration] = DEFAULT_TTL) -> r53.ARecord:
        """Adds a load balancer to the route 53 hosted zone.

        Args:
            id (str): The CDK id of the record to add
            domain_prefix (str): The prefix on the hosted zone domain name e.g. "db"
            load_balancer (elb.ILoadBalancerV2): The LoadBalancer to target.
            comment (Optional[str], optional): [description]. Comment on the route. Defaults to None.
            route_ttl (Optional[Duration], optional): [description]. How long should the route linger. Defaults to DEFAULT_TTL.
        """
        # Create alias target from load balancer
        target = r53_targets.LoadBalancerTarget(
            load_balancer
        )
        # Adds a new record to the hosted zone (or updates current one)
        return r53.ARecord(
            scope=self,
            id=id,
            zone=self.hz,
            record_name=f"{domain_prefix}.{self.root_domain}.",
            comment=comment,
            ttl=route_ttl,
            target=r53.RecordTarget.from_alias(target)
        )

    def add_cname(self,
                  id: str,
                  domain_prefix: str,
                  dns_address: str,
                  comment: Optional[str] = None,
                  route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        """Creates a CName record in the hosted zone, pointing at the specified
        DNS address from the specified domain prefix.

        Args:
            id (str): The CDK Id of the record
            domain_prefix (str): What should the URL prefix look like? e.g. "api"
            dns_address (str): What is the endpoint DNS address.
            comment (Optional[str], optional): Comment on the record. Defaults to None.
            route_ttl (Optional[Duration], optional): How long should the route linger. Defaults to DEFAULT_TTL.
        """
        # Adds a new record to the hosted zone (or updates current one)
        r53.CnameRecord(
            scope=self,
            id=id,
            zone=self.hz,
            record_name=f"{domain_prefix}.{self.root_domain}.",
            domain_name=dns_address,
            comment=comment,
            ttl=route_ttl
        )

    def add_api_gateway_target(
            self,
            id: str,
            target: api_gw.RestApiBase,
            domain_prefix: str,
            comment: Optional[str] = None,
            route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        """
        Function Description
        --------------------

        Generate an API gateway route 53 target


        Arguments
        ----------
        id : str
            The construct id
        target : api_gw.RestApiBase
            The Rest API created through API Gateway
        domain_prefix : str
            The domain prefix e.g. "api"
        comment : Optional[str], optional
            Description/comment, by default None
        route_ttl : Duration[str], optional
            The duration of the route, by default DEFAULT_TTL




        See Also (optional)
        --------

        Examples (optional)
        --------

        """
        r53.ARecord(
            self, id,
            target=r53.RecordTarget.from_alias(r53_targets.ApiGateway(target)),
            zone=self.hz,
            record_name=f"{domain_prefix}.{self.root_domain}.",
            comment=comment,
            ttl=route_ttl)

    def add_cloudfront_distribution_target(
            self,
            id: str,
            sub_domain: str,
            target: cloudfront.Distribution,
            comment: Optional[str] = None,
            route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        """
        Function Description
        --------------------

        Add a route 53 record pointing to cloud front distribution.


        Arguments
        ----------
        id : str
            The construct id
        sub_domain : str
            The domain to point to e.g. "data"
        target : cloudfront.Distribution
            The distribution to target
        comment : Optional[str], optional
            Route comment, by default None
        route_ttl : Optional[Duration], optional
            Route time to live, by default DEFAULT_TTL




        See Also (optional)
        --------

        Examples (optional)
        --------

        """
        r53.ARecord(
            self, id,
            target=r53.RecordTarget.from_alias(
                r53_targets.CloudFrontTarget(target)),
            zone=self.hz,
            record_name=f"{sub_domain}.{self.root_domain}.",
            comment=comment,
            ttl=route_ttl)

    def add_apex_cloudfront_distribution_target(
            self,
            id: str,
            target: cloudfront.Distribution,
            comment: Optional[str] = None,
            route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        """
        Function Description
        --------------------

        Add a route 53 record pointing to cloud front distribution.

        This will make an alias A record from the apex domain name 
        e.g. provena.io


        Arguments
        ----------
        id : str
            The construct id
        target : cloudfront.Distribution
            The distribution to target
        comment : Optional[str], optional
            Route comment, by default None
        route_ttl : Optional[Duration], optional
            Route time to live, by default DEFAULT_TTL


        See Also (optional)
        --------

        Examples (optional)
        --------

        """
        r53.ARecord(
            self, id,
            record_name=f"{self.root_domain}.",
            target=r53.RecordTarget.from_alias(
                r53_targets.CloudFrontTarget(target)),
            zone=self.hz,
            comment=comment,
            ttl=route_ttl)

    def add_subdomain_redirect(
            self,
            id: str,
            from_sub_domain: str,
            to_target: str,
            comment: Optional[str] = None,
            route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        r53.CnameRecord(
            self,
            id,
            domain_name=to_target,
            zone=self.hz,
            comment=comment,
            record_name=f"{from_sub_domain}.{self.root_domain}.",
            ttl=route_ttl)
