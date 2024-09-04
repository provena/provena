from aws_cdk import (
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
                 debug_route_prefix: Optional[str] = None,
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
            root_domain (str): The fully qualified root domain of the application
            debug_route_prefix (Optional[str]): DEBUG - A value to prefix to all routes created in order to enable redeployments safely.
        """

        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # the application root domain which routes will be respective to
        self.root_domain = root_domain
        self.debug_route_prefix = debug_route_prefix

        # Pull the existing Hosted Zone based on the hosted_zone_id
        self.hz = r53.PublicHostedZone.from_hosted_zone_attributes(
            scope=self,
            id=construct_id + "_hosted_zone",
            hosted_zone_id=hosted_zone_id,
            zone_name=hosted_zone_name
        )

    def _generate_route(
        self,
        domain: str,
    ) -> str:
        """

        Generates routes sensitive to the application root domain. Used in various functions within this class.

        Parameters
        ----------
        domain : str
            The domain name to prefix

        Returns
        -------
        str
            The full domain name to use
        """
        # Apex record
        if domain == "" and (self.debug_route_prefix is None or self.debug_route_prefix == ""):
            # postfixed with . to be suitable for record name field
            return f"{self.root_domain}."
        else:
            # postfixed with . to be suitable for record name field
            return f"{self.debug_route_prefix or ''}{domain}.{self.root_domain}."

    def add_load_balancer(self,
                          id: str,
                          domain: str,
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
            record_name=self._generate_route(domain),
            comment=comment,
            ttl=route_ttl,
            target=r53.RecordTarget.from_alias(target)
        )

    def add_cname(self,
                  id: str,
                  domain: str,
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
            record_name=self._generate_route(domain),
            domain_name=dns_address,
            comment=comment,
            ttl=route_ttl
        )

    def add_api_gateway_target(
            self,
            id: str,
            target: api_gw.RestApiBase,
            domain: str,
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
            record_name=self._generate_route(domain),
            comment=comment,
            ttl=route_ttl)

    def add_cloudfront_distribution_target(
            self,
            id: str,
            domain: str,
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
            record_name=self._generate_route(domain),
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
            from_domain: str,
            to_domain: str,
            comment: Optional[str] = None,
            route_ttl: Optional[Duration] = DEFAULT_TTL) -> None:
        r53.CnameRecord(
            self,
            id,
            domain_name=self._generate_route(to_domain),
            zone=self.hz,
            comment=comment,
            record_name=self._generate_route(from_domain),
            ttl=route_ttl)
