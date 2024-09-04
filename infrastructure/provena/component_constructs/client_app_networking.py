from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_elasticloadbalancingv2_targets as elb_targets,
    aws_elasticloadbalancingv2_actions as elb_actions,
    Duration
)

from constructs import Construct
from typing import Any, List
from provena.custom_constructs.service_instance import ServiceInstance
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.load_balancers import SharedBalancers


# NOTE this is deprecated - no longer being used however the pattern is retained
# for potential future use

class ClientAppNetworking(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: ec2.IVpc,
            allocator: DNSAllocator,
            balancers: SharedBalancers,
            https_priority: int,
            http_priority: int,
            sub_domain: str,
            cert_arn: str,
            application_http_traffic_port: int,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # setup the service instance
        service_instance = ServiceInstance(
            scope=self,
            id='instance',
            vpc=vpc,
            static_ip=True,
            size=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.T3,
                instance_size=ec2.InstanceSize.MEDIUM
            )
        )

        # pull out ec2 instance interface
        instance = service_instance.instance

        # Create a basic target group with HTTP health checks
        tg = elb.ApplicationTargetGroup(
            self,
            f"tg",
            port=application_http_traffic_port,
            protocol=elb.ApplicationProtocol.HTTP,
            target_type=elb.TargetType.INSTANCE,
            health_check=elb.HealthCheck(
                # health check must be enabled for target groups with instance type
                enabled=True,
                healthy_http_codes="200",
                protocol=elb.Protocol.HTTP,
                port=str(application_http_traffic_port),
                timeout=Duration.seconds(10),
                healthy_threshold_count=5,
                unhealthy_threshold_count=5,
                interval=Duration.seconds(30)
            ),
            vpc=vpc
        )

        # Register the instance target in the target group
        target = elb_targets.InstanceTarget(
            instance=instance,
            port=application_http_traffic_port
        )
        tg.add_target(target)

        # Enable traffic from the ALB -> instance
        assert balancers.alb
        instance.connections.allow_from(balancers.alb, port_range=ec2.Port.tcp_range(
            application_http_traffic_port, application_http_traffic_port))

        # make sure balancers is setup

        # Make sure https listener is setup
        if balancers.https_listener is None:
            balancers.setup_https_listener(
                certificates=[]
            )

        # Make sure http listener is setup
        if balancers.http_listener is None:
            balancers.setup_http_listener()

        # add required cert for https traffic
        balancers.add_https_certificates(
            id='neo4j-certs',
            certificates=[elb.ListenerCertificate.from_arn(cert_arn)]
        )

        # Add a listener action on the subdomain
        # expected domain
        expected_header = f"{sub_domain}.{allocator.root_domain}"
        balancers.add_http_redirected_conditional_https_target(
            action_id='neo4j',
            target_group=tg,
            conditions=[
                elb.ListenerCondition.host_headers([expected_header])
            ],
            priority=https_priority,
            http_redirect_priority=http_priority
        )

        # now register a domain in the allocator
        assert balancers.alb
        allocator.add_load_balancer(
            id='client-balancer-route',
            domain=sub_domain,
            load_balancer=balancers.alb,
            comment='Routes HTTPS traffic for client tool'
        )
